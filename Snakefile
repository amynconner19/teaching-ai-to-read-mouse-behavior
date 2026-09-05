"""Run both pretrained BIOMAP DeepLabCut models on a folder of videos."""

from pathlib import Path


configfile: "config/config.yaml"


VIDEO_DIR = Path(config["video_dir"])
OUTPUT_DIR = config["output_dir"].rstrip("/")
VIDEO_EXTENSIONS = {
    extension.lower() if extension.startswith(".") else f".{extension.lower()}"
    for extension in config.get("video_extensions", [".avi"])
}
MODELS = sorted(config["models"])


def discover_videos():
    """Return a mapping from unique video stem to source path."""
    if not VIDEO_DIR.is_dir():
        raise WorkflowError(
            f"Video directory does not exist: {VIDEO_DIR}. "
            "Create it or change video_dir in the selected config file."
        )

    videos = {}
    for path in sorted(VIDEO_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            if path.stem in videos:
                raise WorkflowError(
                    f"Two input videos have the same filename stem: {path.stem}. "
                    "Rename one video so standardized outputs remain unique."
                )
            videos[path.stem] = str(path)

    if not videos:
        extensions = ", ".join(sorted(VIDEO_EXTENSIONS))
        raise WorkflowError(
            f"No supported videos found in {VIDEO_DIR}. Expected: {extensions}."
        )
    return videos


VIDEOS = discover_videos()
SAMPLES = sorted(VIDEOS)


rule all:
    input:
        expand(
            f"{OUTPUT_DIR}/{{model}}/{{sample}}.csv",
            model=MODELS,
            sample=SAMPLES,
        )


rule run_deeplabcut:
    input:
        video=lambda wildcards: VIDEOS[wildcards.sample],
        model_config=lambda wildcards: config["models"][wildcards.model]["config"],
    output:
        csv=f"{OUTPUT_DIR}/{{model}}/{{sample}}.csv",
    log:
        f"{OUTPUT_DIR}/logs/{{model}}/{{sample}}.log",
    params:
        device=lambda wildcards: config.get("device", "cpu"),
        shuffle=lambda wildcards: config["models"][wildcards.model].get("shuffle", 1),
        trainingsetindex=lambda wildcards: config["models"][wildcards.model].get(
            "trainingsetindex", 0
        ),
        batch_size=lambda wildcards: config["models"][wildcards.model].get(
            "batch_size", config.get("batch_size", 1)
        ),
    threads: 1
    conda:
        "workflow/envs/deeplabcut.yaml"
    shell:
        """
        python workflow/scripts/run_deeplabcut.py \
            --config {input.model_config:q} \
            --video {input.video:q} \
            --output {output.csv:q} \
            --device {params.device:q} \
            --shuffle {params.shuffle} \
            --trainingsetindex {params.trainingsetindex} \
            --batch-size {params.batch_size} \
            2>&1 | tee {log:q}
        """
