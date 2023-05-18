#
# Copyright (C) 2020-2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
#

import os
import logging as log
from adaptors.base_adaptor import BaseInterface
from adaptors.ovtoolkit.load_model import ModelLoader
import datetime
import sys
import openvino.runtime as ov

class OvtkInterface(BaseInterface):
    def __init__(self, model_name, path, device):
        super().__init__()
        self.ie = ov.Core()
        self.device = device
        self.net = ''
        self.exec_net = ''
        self.model_loader = ModelLoader(str(model_name))
        self.model_loader.setModelDir(path)
        self.infer_request = ''

    def load_model(self, model_xml=None, model_name=None):
        if not model_xml:
            log.error("Error !!! model_xml path: \'{}\' missing".format(model_xml))
            sys.exit(1)

        # ---------- 1. Read IR Generated by ModelOptimizer (.xml and .bin files) -------------
        model_bin = os.path.splitext(model_xml)[0] + ".bin"
        log.info("loading network files:\n\t{}\n\t{}".format(model_xml, model_bin))
        self.net = self.ie.read_model(model=model_xml, weights=model_bin)
        log.info("using device: "+ self.device)
        tput = {'PERFORMANCE_HINT': 'LATENCY'}
        self.exec_net = self.ie.compile_model(self.net, self.device, tput)
        self.infer_request = self.exec_net.create_infer_request()
        log.info("infer request created for model: {}".format(model_name))

        return 30          #AVAILABLE

    def run_detection(self, input_data):
        start_time = datetime.datetime.now()

        processed_data = {}
        for key in input_data:
            input_shape = input_data[key][1]
            img = input_data[key][0]
            img = img.reshape(input_shape)
            processed_data[int(key)] = img

        curr_time = datetime.datetime.now()
        if (self.infer_request == '') :
            log.error("Error !!! infer request is null")
            sys.exit(1)
        res = self.infer_request.infer(inputs=processed_data)
        end_time = datetime.datetime.now()
        predict_time = (end_time - curr_time).total_seconds() * 1000
        #returns dictionary with keyword as nodename and values :tupple of data and their shape
        response = {}
        for output_key in range(len(self.exec_net.outputs)):
            out = self.infer_request.get_output_tensor(output_key).data
            response[str(output_key)] = (out, list(out.shape))
        exit_time = datetime.datetime.now()
        input_time = (curr_time - start_time).total_seconds() * 1000
        output_time = (exit_time - end_time).total_seconds() * 1000
        print("INPUT_Prep:{} Inference_TIME:{} OUTPUT_Prep:{}".format(input_time,
                                                                      predict_time, output_time))
        return response

    def prepareDir(self):
        self.model_loader.prepareDir()

    def cleanUp(self):
        self.model_loader.cleanUp()

    def saveXML(self, chunk):
        self.model_loader.saveXML(chunk)

    def saveBin(self, chunk):
        self.model_loader.saveBin(chunk)

    def isModelLoaded(self, timeout_in_ms):
        return self.model_loader.isModelLoaded(self, timeout_in_ms)
