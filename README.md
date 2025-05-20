# 🧪 Per-Object Flowrate Calibration for Bambu Studio (H2D)

This script provides a workaround for calibrating flow rate on the **Bambu Lab H2D**, which is currently **not supported in OrcaSlicer**. OrcaSlicer recently introduced a new top surface pattern to simplify flow calibration, but without H2D support, we can’t use it directly.

**Bambu Studio** also lacks per-object flowrate settings, so this script performs post-processing on the exported G-code to apply different flow rates per object — ideal for running flow calibration prints.

---

## 📦 What’s Included

- Two `.3mf` files: These are the **YOLO version** (linear flow test) exported from OrcaSlicer, using a custom profile tailored for the H2D.

- A Python script: `per_object_flowrate.py`  
  This modifies the G-code to apply calibrated flow rates per object.

  The logic mirrors the implementation in OrcaSlicer:  
  [OrcaSlicer/plater.cpp#L9855](https://github.com/SoftFever/OrcaSlicer/blob/00277ac4b0b33133b5190af4b05df33a58094d76/src/slic3r/GUI/Plater.cpp#L9855)

---

## ⚙️ How to Use

1. **Open the `.3mf` file** in **Bambu Studio**.
2. **Slice** the project after selecting the filament you want to calibrate.
3. **Export** the G-code to your local drive.
4. Run the script:

   ```bash
   python3 ./per_object_flowrate.py -g flowrate_1.gcode -p 1 -s 24
   ```

   - `-g`: Path to your exported G-code file  
   - `-p`: The pass index (use `1` for the first pass, `2` for the second pass)  
   - `-s`: Maximum volumetric speed of the filament (in mm³/s)

5. After modifying the G-code, you may want to **adjust the slicer’s top surface speed and solid infill speed**, since these are tied to the filament's volumetric limit.

    - If the **top surface speed and solid infill speed** need changing, then start over from **step 1** after changing the settings.

6. **Send the modified G-code to your H2D** — via **USB flash drive** (required for the send function to work in Bambu Studio).

---

## 🎯 Important Notes

- When slicing make sure to have only **ONE** filament listed under the **Project Filaments** section in Bambu Studio.
- The filament must be loaded in the left nozzle (for some reason it won't let you change to the right nozzle).
- This script is intended for use with **flow calibration prints**, not general models.
- This script only supports **0.4mm nozzles** and **0.2mm layer height** for now (will add more command line arguments later).
