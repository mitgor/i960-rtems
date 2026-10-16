# Tetris: playable card application

Tetris runs on the i960 through returning firmware callbacks. Linux forwards
keys and displays the card's ASCII framebuffer. This established application
does **not** require RTEMS.

- [Source directory and offline checks](../../game/tetris/README.md).
- Core: [tetris.c](../../game/tetris/tetris.c), [interface](../../game/tetris/tetris.h), [build](../../game/tetris/Makefile).
- Payload and I/O: [runtime loader](../../loader/runtime/README.md), [bounded step](../../docs/games/TETRIS-STEP.md).
- Frontend: [host/session](../../host/session/README.md), [terminal instructions](../../docs/games/TETRIS-TERMINAL.md).
- Exact accepted source/binaries/results: [T4](../../artifacts/notes/tetris-t4-20261010.md), [T5 transport](../../artifacts/notes/tetris-t5-20261010.md).

On the existing deployment, after the card's current owner has stopped safely:

```sh
ssh -t mit@192.168.2.75 /home/mit/i960-tetris-t4/play.sh
```

Use an 80×24 terminal. A/D or arrows move; W/Up rotates; S/Down/Space drops;
R restarts; Q/Ctrl-C quits. The launcher refuses an already owned card.
For a new machine, follow the terminal guide and preserved build evidence;
the deployed path above is not a fresh-checkout build command.

The acceptance run completed 35,846 native-matching frames over 30 minutes at
19.91 Hz, including restart, disconnect/reconnect and terminal cleanup tests.
