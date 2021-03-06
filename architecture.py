# imports
from typing import Tuple, Dict, List
import torch
import torch.nn as nn

class DetectionLayer(nn.Module):
    def __init__(self, anchor):
        super(DetectionLayer, self).__init__()
        self.anchors = anchor

class Empty(nn.Module):
    def __init__(self):
        super(Empty, self).__init__()

def construct(blocks: List) -> Tuple[dict, torch.nn.ModuleList]:
    moduleList = nn.ModuleList()
    output_filters = []
    prev_filters = 3
    idx = 0

    for _, layer in enumerate(blocks):
        modules = nn.Sequential()

        if layer['arch'] == 'net':
            continue

        if layer['arch'] == 'convolutional':
            activation = layer['activation']
            filters = int(layer['filters'])
            stride = int(layer['stride'])
            kernel = int(layer['size'])
            padding = int(layer['pad'])

            if padding:
                pad = (kernel - 1) // 2
            try:
                batch_norm = int(layer['batch_normalize'])
                bias = False
            except:
                batch_norm = 0
                bias = True
            
            conv = nn.Conv2d(prev_filters, filters, kernel, stride, pad, bias = bias)
            modules.add_module(f"conv_{idx}", conv)

            if batch_norm:
                modules.add_module(f"bn_{idx}", nn.BatchNorm2d(filters))
            
            if activation == "leaky":
                modules.add_module(f"leaky_{idx}", nn.LeakyReLU(0.1, inplace = True))
        
        elif layer['arch'] == 'upsample':
            # stride = int(layer['stride'])
            upsample = nn.Upsample(scale_factor = 2, mode = 'nearest')
            modules.add_module(f"upsample_{idx}", upsample)

        elif layer['arch'] == 'shortcut':
            empty = Empty()
            modules.add_module(f"shortcut_{idx}", empty)
        
        elif layer['arch'] == 'route':
            layer['layers'] = layer['layers'].split(',')
            start = int(layer['layers'][0])
            try:
                end = int(layer['layers'][1])
            except:
                end = 0
            
            if start > 0:
                start -= idx
            if end > 0:
                end -= idx
            
            route = Empty()
            modules.add_module(f"route_{idx}", route)
            
            if end < 0:
                filters = output_filters[start + idx] + output_filters[idx + end]
            else:
                filters = output_filters[start + idx]
            
        elif layer['arch'] == 'yolo':
            mask = layer['mask'].split(',')
            mask = [int(m) for m in mask]
 
            anchors = layer['anchors'].split(',')
            anchors = [int(a) for a in anchors]
            anchors = [(anchors[i], anchors[i+1]) for i in range(0, len(anchors), 2)]
            anchors = [anchors[m] for m in mask]

            detect = DetectionLayer(anchors)
            modules.add_module(f"Detection_{idx}", detect)

        moduleList.append(modules)
        prev_filters = filters
        output_filters.append(filters)
        idx += 1
    
    return (blocks[0], moduleList)

