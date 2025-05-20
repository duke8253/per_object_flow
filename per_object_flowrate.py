#!/usr/bin/env python3

import argparse
import os
from collections import defaultdict
import math

class PerObjFlow:

    def __init__(self, f_path='', cali_pass=1, mv_speed=0):
        self.f_path = f_path
        self.f_dir = os.path.dirname(self.f_path)
        self.f_name = os.path.basename(self.f_path)
        self.f_name_per_obj = f'{self.f_name.split('.')[0]}_per_obj.gcode'

        self.cali_pass = cali_pass
        self.flow_seq = []

        if self.cali_pass == 1:
            flow_diff = 0.01
            curr_flow = 0
            for i in range(11):
                self.flow_seq.append(curr_flow)
                if i == 5:
                    curr_flow = 0
                    flow_diff = -0.01
                curr_flow += flow_diff
        else:
            flow_diff = 0.005
            curr_flow = 0
            for i in range(16):
                self.flow_seq.append(curr_flow)
                if i == 7:
                    curr_flow = 0
                    flow_diff = -0.005
                curr_flow += flow_diff

        self.gcode_data = self.read_gcode_file()
        self.model_info = self.get_model_info()
        self.obj_flow = self.calc_flow_ratios()

        if mv_speed > 0:
            modifier = 0.05 if self.cali_pass == 1 else 0.035
            layer_height = 0.2
            nozzle_diameter = 0.4
            line_width = nozzle_diameter * 1.2
            infill_speed = mv_speed / ((layer_height * (line_width - layer_height * (1 - 0.25 * math.pi))) * (modifier + self.model_info['base_flowrate']) / self.model_info['base_flowrate'])

            settings_str = \
                f'Please set the following settings in the slicer:\n' + \
                f'Line width:\n' + \
                f'    Top surface: {line_width}\n' + \
                f'    Internal solid infill: {line_width}\n' + \
                f'Speed:\n' + \
                f'    Top surface: {min(self.model_info['top_surface_speed'], math.floor(infill_speed))}\n' + \
                f'    Internal solid infill: {min(self.model_info['internal_solid_infill_speed'], math.floor(infill_speed))}\n'
            print(settings_str)

        self.change_flow_ratios()
        self.write_gcode_file()

        return

    def read_gcode_file(self):
        with open(self.f_path, 'r') as f_read:
            data = f_read.readlines()
        return data

    def write_gcode_file(self):
        f_path_per_obj = os.path.join(self.f_dir, self.f_name_per_obj)
        with open(f_path_per_obj, 'w') as f_write:
            f_write.writelines(self.gcode_data)
        return

    def get_model_info(self):
        model_info = {}
        for line in self.gcode_data:
            if line.startswith('; model label id'):
                obj_ids = line.split(':')[-1].strip().split(',')
                if len(obj_ids) != len(self.flow_seq):
                    print('Object read wrong.')
                    exit(1)
                model_info['obj_ids'] = obj_ids

            elif line.startswith('; filament_flow_ratio'):
                base_flowrate = float(line.split('=')[-1].strip().split(',')[0])
                model_info['base_flowrate'] = base_flowrate

            elif line.startswith('; internal_solid_infill_speed'):
                model_info['internal_solid_infill_speed'] = math.floor(float(line.split('=')[-1].strip().split(',')[0]))

            elif line.startswith('; top_surface_speed'):
                model_info['top_surface_speed'] = math.floor(float(line.split('=')[-1].strip().split(',')[0]))

            if len(model_info) == 4:
                break
        return model_info

    def calc_flow_ratios(self):
        obj_flow = {}
        base_flowrate = self.model_info['base_flowrate']

        for i in range(len(self.flow_seq)):
            obj_id = self.model_info['obj_ids'][i]
            flowrate_diff = self.flow_seq[i]
            obj_flow[obj_id] = (base_flowrate + flowrate_diff) / base_flowrate
        return obj_flow

    def change_flow_ratios(self):
        curr_obj_id = ''

        for i in range(len(self.gcode_data)):
            line = self.gcode_data[i]
            if line.startswith('; start printing object, unique label id'):
                obj_id = line.split(':')[1].strip()
                curr_obj_id = obj_id
            elif line.startswith('; stop printing object, unique label id'):
                curr_obj_id = ''
            elif curr_obj_id != '' and line.startswith('G') and 'E' in line and ('X' in line or 'Y' in line):
                new_cmd = line.split()
                change_flag = False
                for j in range(len(new_cmd)):
                    if new_cmd[j].startswith('E'):
                        old_flow = float(new_cmd[j][1:])
                        if old_flow < 0:
                            break
                        new_flow = round(old_flow * self.obj_flow[curr_obj_id], 5)
                        new_cmd[j] = f'E{new_flow:}'.replace('E0.', 'E.')
                        change_flag = True
                        break

                if change_flag:
                    self.gcode_data[i] = ' '.join(new_cmd) + '\n'

def main():
    parser = argparse.ArgumentParser(
        prog='BSFCP',
        description='Bambu Studio flowrate calibration postprocessing.',
    )

    parser.add_argument('-g', '--gcode', dest='gcode_f_path', type=str, required=True, help='Path of the gcode file.')
    parser.add_argument('-p', '--pass', dest='cali_pass', type=int, choices=[1, 2], default=1, help='Which calibrationpass this is.')
    parser.add_argument('-s', '--speed', dest='speed', type=float, required=False, default=0, help='Max volumetric speed for calculating top surface and solid infill speed.')
    args = parser.parse_args()

    per_obj_flow = PerObjFlow(args.gcode_f_path, args.cali_pass, args.speed)

if __name__ == '__main__':
    main()
