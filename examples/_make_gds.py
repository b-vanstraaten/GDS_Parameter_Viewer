from pathlib import Path

import klayout.db as kl

layout = kl.Layout()


def make_gds(path: Path):

    # Define layers
    barriers = layout.layer(0, 0)
    plungers = layout.layer(1, 0)

    top = layout.create_cell("TOP")

    barrier = kl.Box(-25, -50, 25, 50)
    top.shapes(barriers).insert(barrier)

    plunger_1 = kl.Box(-125, -50, -25, 50)
    top.shapes(plungers).insert(plunger_1)

    plunger_2 = kl.Box(25, -50, 125, 50)
    top.shapes(plungers).insert(plunger_2)

    layout.write(path)
    print("GDS file written successfully")