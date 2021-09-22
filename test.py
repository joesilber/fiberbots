#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 15:28:27 2021

@author: ldrd
"""

import sys
sys.path.append('motors')
from tendo import Positioners
pos = Positioners()
pos.connect()