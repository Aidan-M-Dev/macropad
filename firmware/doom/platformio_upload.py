import os
from pathlib import Path
import subprocess

Import("env")

project_dir = Path(env.subst("$PROJECT_DIR"))
doom_dir = project_dir / "doom"
pack_script = doom_dir / "pack.sh"
doom_binary = doom_dir / "doom_tiny.bin"
combined_path = "$BUILD_DIR/ichack-combined.uf2"


def pack_combined(target, source, env):
    platform = env.PioPlatform()
    toolchain = Path(platform.get_package_dir("toolchain-rp2040-earlephilhower"))
    pack_env = {
        **os.environ,
        "OBJCOPY": str(toolchain / "bin" / env.subst("$OBJCOPY")),
        "PICOTOOL": env.subst("$UPLOADER"),
    }
    return subprocess.run(
        ["sh", str(pack_script), source[0].abspath, source[1].abspath, target[0].abspath],
        env=pack_env,
    ).returncode


combined = env.Command(
    combined_path,
    ["$BUILD_DIR/${PROGNAME}.elf", str(doom_binary), str(pack_script)],
    env.VerboseAction(pack_combined, "Packing keyboard, Pong, Breakout and Doom"),
)
env.AddCustomTarget("combined", combined, None, "Build combined firmware")
env.Depends("upload", combined)
env.Replace(UPLOADCMD=f'"$UPLOADER" load $UPLOADERFLAGS "{combined_path}"')
