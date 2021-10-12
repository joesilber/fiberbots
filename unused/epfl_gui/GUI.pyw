#cython: language_level=3
import PySimpleGUI as sg
import numpy as np
import DEFINES
import classCanCom as canCom
import errors
import traceback
import time

class ManualControlWindow:
	def __init__(self):

		self.comHandle = canCom.COM_handle()
		self.currentCanUSBserial = ''
		self.availableCanComSerials = []

		self.availablePositionerIDs = []
		self.selectedPositionerIDs = []

		self.bootloaderMotorPolarityList = ['Normal', 'Reversed']
		self.bootloaderCountdown = 0
		self.bootloaderIsRoot = []
		self.IDchanged = False

		self.positionerMovementTime = 0

		self.GUItimeout = 0
		
		sg.ChangeLookAndFeel('Dark')

		self.layout = 	[	
							[	sg.Column(
									[	
										[	sg.Frame('CAN-USB',
												[
													[	sg.Combo 	( 	self.availableCanComSerials,
																		key = 'CanUSBSerialsCombo',
																		size = (9,1),
																		tooltip = 'Select the CAN-USB serial number'),
														sg.Button 	( 	'Refresh',
																		key = 'refreshCanUSBSerialsButton',
																		enable_events = True, 
																		size = (7,1),
																		button_color = ('black', '#8080EE'),
																		tooltip = 'Refresh the CAN-USB list')							
													],
													[	sg.Text 	(	'Status: ',
																		font = (DEFINES.GUI_DEFAULT_FONT, 10),
																		justification='left',
																		size = (6,1)),
														sg.Text 	(	'Disconnected',
																		justification='left',
																		size = (13,1),
																		relief = sg.RELIEF_SUNKEN,
																		key = 'canUSBStatusText',
																		tooltip = 'Current connexion status')
													],
													[	sg.Button 	( 	'Connect',
																		key = 'connectCanUSBButton',
																		enable_events = True, 
																		size = (9,1),
																		button_color = ('black', '#90EE90'),
																		disabled = not len(self.availableCanComSerials),
																		tooltip = 'Connect to the selected CAN-USB'),
														sg.Button 	( 	'Disconnect',
																		key = 'disconnectCanUSBButton',
																		enable_events = True, 
																		size = (9,1),
																		button_color = ('black', '#EE9090'),
																		disabled = not len(self.availableCanComSerials),
																		tooltip = 'Disconnect from the connected CAN-USB')
													]										
												]
											, pad = ((0,0),(0,0)))
										],
										[	sg.Frame('Positioners',
												[
													[	sg.Button 	( 	'Refresh and select all',
																		key = 'refreshPositionersButton',
																		enable_events = True, 
																		size = (20,1),
																		button_color = ('black', '#8080EE'),
																		tooltip = 'Refresh the positioner IDs list')							
													],
													[	sg.Listbox	(	self.availablePositionerIDs,
																		size = (21,20), 
																		default_values = self.selectedPositionerIDs,
																		select_mode = sg.LISTBOX_SELECT_MODE_MULTIPLE,
																		enable_events = True,
																		key = 'selectPositionersListbox',
																		tooltip = 'Select the positioners to send the commands to.\nSelected positioners are in Blue.')
													],
													[	sg.Button 	( 	'Reboot',
																		key = 'rebootPositionersButton',
																		enable_events = True, 
																		size = (20,1),
																		button_color = ('black', '#EEEE80'),
																		tooltip = 'Reboot the positioners')
													]
												]
											, pad = ((0,0),(0,0)))											
										],
										[	sg.Frame('General',
												[
													[	sg.Button 	( 	'Exit manual control',
																		key = 'GeneralExitButton',
																		enable_events = True, 
																		size = (20,2),
																		button_color = ('black', '#EE6060'),
																		tooltip = 'Exit the manual control')							
													]						
												]
											, pad = ((0,0),(0,0)))											
										]										
									]
								, pad = ((0,0),(0,0))),
								sg.Column(
									[	
										[	sg.Frame('Control Panel',
												[	
													[	sg.Column(
															[
																[	sg.Button 	( 	'Boot',
																					key = 'bootPositionersButton',
																					enable_events = True, 
																					size = (20,1),
																					button_color = ('black', '#80EE80'),
																					tooltip = 'Exit the bootloader')
																],
																[	sg.Text 	(	'Bootloader exits in ',
																					font = (DEFINES.GUI_DEFAULT_FONT, 10),
																					justification='left',
																					key = 'positionerBootloaderTimerText1',
																					size = (18,1)),
																	sg.Text 	(	'00.00',
																					justification='right',
																					size = (6,1),
																					relief = sg.RELIEF_SUNKEN,
																					key = 'positionerBootloaderTimerText',
																					tooltip = 'Remaining time before automatic boot'),
																	sg.Text 	(	'[s]',
																					font = (DEFINES.GUI_DEFAULT_FONT, 10),
																					justification='left',
																					key = 'positionerBootloaderTimerText2',
																					size = (2,1)),
																	sg.Checkbox (	'Autorefresh',
																					default = True,
																					key = 'positionerBootloaderTimerAutorefreshCheckbox',
																					tooltip = 'Forbids the positioners to make an automated boot.\nConstantly refreshes the status.'),
																],
																[	sg.Frame('Bootloader parameters',
																		[
																			[	sg.Text 	(	'',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								size = (18,1)),
																				sg.Text 	(	'General parameters',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								key = 'positionerBLGeneralText',																								
																								justification='left',
																								size = (20,1)),
																				sg.Button 	( 	'Set all',
																								key = 'positionerBLSetAllButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Sends all the parameters to all the positioners.\nThe ID is sent only to the first positioner.\nChanges becomes effective once the positioners boot.'),
																				sg.Button 	( 	'Get all',
																								key = 'positionerBLGetAllButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves all the parameters from the first positioner.')

																			],
																			[	sg.Text 	(	'Positioner ID',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBL_IDText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(1,2047)),
																								initial_value = 1,
																								key = 'positionerBL_IDSpin',
																								size = (9,1),
																								tooltip = 'Change the ID of the first positioner.'),
																				sg.Text 	(	'',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								size = (9,1)),
																				sg.Button 	( 	'Set',
																								key = 'positionerBL_IDSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the new ID to the first positioner.\nChange becomes effective once the positioner boots."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBL_IDGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the ID from the first positioner.')
																			],
																			[	sg.Text 	(	'',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								size = (18,1)),
																				sg.Text 	(	'Alpha',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='center',
																								key = 'positionerBLAlphaText',
																								size = (9,1)),
																				sg.Text 	(	'Beta',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='center',
																								key = 'positionerBLBetaText',
																								size = (9,1))
																			],
																			[	sg.Text 	(	'Reduction ratio (1:n)',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLReductionRatioText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = 1024,
																								enable_events = True,
																								key = 'positionerBLReductionRatioAlphaSpin',
																								size = (9,1),
																								tooltip = 'The alpha motor reduction ratio.'),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = 1024,
																								enable_events = True,
																								key = 'positionerBLReductionRatioBetaSpin',
																								size = (9,1),
																								tooltip = 'The beta motor reduction ratio.'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLReductionRatioSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the motor reduction ratios to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLReductionRatioGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the motor reduction ratios from the first positioner.')
																			],
																			[	sg.Text 	(	'Motor polarity',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLPolarityText',
																								size = (18,1)),
																				sg.Combo 	(	self.bootloaderMotorPolarityList,
																								default_value = 'Normal',
																								key = 'positionerBLPolarityAlphaCombo',
																								size = (9,1),
																								tooltip = 'The alpha motor polarity.\nUse this parameter to toggle the rotation direction of the output.'),
																				sg.Combo 	(	self.bootloaderMotorPolarityList,
																								default_value = 'Normal',
																								key = 'positionerBLPolarityBetaCombo',
																								size = (9,1),
																								tooltip = 'The beta motor polarity.\nUse this parameter to toggle the rotation direction of the output.'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLPolaritySetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the motor polarities to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLPolarityGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the motor polarities from the first positioner.')
																			],
																			[	sg.Text 	(	'Motor maximal speed',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLMaxSpeedText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = 5000,
																								key = 'positionerBLMaxSpeedAlphaSpin',
																								size = (9,1),
																								tooltip = 'The alpha motor maximal speed [RPM].'),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = 5000,
																								key = 'positionerBLMaxSpeedBetaSpin',
																								size = (9,1),
																								tooltip = 'The beta motor maximal speed [RPM].'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLMaxSpeedSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the motor maximal speeds to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLMaxSpeedGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the motor maximal speeds from the first positioner.')
																			],
																			[	sg.Text 	(	'Motor maximal current',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLMaxCurrentText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = 70,
																								key = 'positionerBLMaxCurrentAlphaSpin',
																								size = (9,1),
																								tooltip = 'The alpha motor maximal open loop current [%].'),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = 70,
																								key = 'positionerBLMaxCurrentBetaSpin',
																								size = (9,1),
																								tooltip = 'The beta motor maximal open loop current [%].'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLMaxCurrentSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the motor maximal open loop currents to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLMaxCurrentGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the motor maximal open loop currents from the first positioner.')
																			],
																			[	sg.Text 	(	'Lower position limit',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLLowRangeLimitText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(-720,720)),
																								initial_value = 0,
																								key = 'positionerBLLowRangeLimitAlphaSpin',
																								size = (9,1),
																								tooltip = 'The alpha output lower angle limit [°].'),
																				sg.Spin 	(	list(range(-720,720)),
																								initial_value = 0,
																								key = 'positionerBLLowRangeLimitBetaSpin',
																								size = (9,1),
																								tooltip = 'The beta output lower angle limit [°].'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLLowRangeLimitSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the output lower angle limits to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLLowRangeLimitGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the output lower angle limits from the first positioner.')
																			],
																			[	sg.Text 	(	'Upper position limit',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerBLHighRangeLimitText',
																								size = (18,1)),
																				sg.Spin 	(	list(range(-720,720)),
																								initial_value = 0,
																								key = 'positionerBLHighRangeLimitAlphaSpin',
																								size = (9,1),
																								tooltip = 'The alpha output upper angle limit [°].'),
																				sg.Spin 	(	list(range(-720,720)),
																								initial_value = 0,
																								key = 'positionerBLHighRangeLimitBetaSpin',
																								size = (9,1),
																								tooltip = 'The beta output upper angle limit [°].'),
																				sg.Button 	( 	'Set',
																								key = 'positionerBLHighRangeLimitSetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = "Sends the output upper angle limits to all positioners.\nChanges become effective once the positioners boot."),
																				sg.Button 	( 	'Get',
																								key = 'positionerBLHighRangeLimitGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the output upper angle limits from the first positioner.')
																			]
																		]
																	, pad = ((0,0),(0,0)))
																]														
															]
														, pad = ((0,0),(0,0))),
														sg.Column(
															[
																[	sg.Frame('Positioner control',
																		[
																			[	sg.Text 	(	'',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								size = (25,1)),
																				sg.Text 	(	'Alpha',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='center',
																								key = 'positionerNormalAlphaText',
																								size = (7,1)),
																				sg.Text 	(	'Beta',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='center',
																								key = 'positionerNormalBetaText',
																								size = (7,1))
																			],
																			[	sg.Text 	(	'Open loop current',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerOpenLoopCurrentText',
																								size = (25,1)),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = DEFINES.DEFAULT_OPEN_LOOP_CURRENT,
																								enable_events = True,
																								key = 'positionerOpenLoopCurrentAlphaSpin',
																								size = (7,1),
																								tooltip = 'The alpha motor open loop current [%]'),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = DEFINES.DEFAULT_OPEN_LOOP_CURRENT,
																								enable_events = True,
																								key = 'positionerOpenLoopCurrentBetaSpin',
																								size = (7,1),
																								tooltip = 'The beta motor open loop current [%]'),
																				sg.Button 	( 	'Send',
																								key = 'positionerOpenLoopCurrentSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the motor open loop currents to all the positioners.')
																			],
																			[	sg.Text 	(	'Holding current',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerHoldingCurrentText',
																								size = (25,1)),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = DEFINES.DEFAULT_HOLDING_CURRENT,
																								enable_events = True,
																								key = 'positionerHoldingCurrentAlphaSpin',
																								size = (7,1),
																								tooltip = 'The alpha motor holding current [%].\nThis is the current used after the moves in low power mode.'),
																				sg.Spin 	(	list(range(1,101)),
																								initial_value = DEFINES.DEFAULT_HOLDING_CURRENT,
																								enable_events = True,
																								key = 'positionerHoldingCurrentBetaSpin',
																								size = (7,1),
																								tooltip = 'The beta motor holding current [%].\nThis is the current used after the moves in low power mode.'),
																				sg.Button 	( 	'Send',
																								key = 'positionerHoldingCurrentSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the motor holding currents to all the positioners.')
																			],
																			[	sg.Text 	(	'Motor speed',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerMotorSpeedText',
																								size = (25,1)),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = DEFINES.DEFAULT_MOTOR_SPEED,
																								enable_events = True,
																								key = 'positionerMotorSpeedAlphaSpin',
																								size = (7,1),
																								tooltip = 'The alpha motor speed [RPM]'),
																				sg.Spin 	(	list(range(1,65536)),
																								initial_value = DEFINES.DEFAULT_MOTOR_SPEED,
																								enable_events = True,
																								key = 'positionerMotorSpeedBetaSpin',
																								size = (7,1),
																								tooltip = 'The beta motor speed [RPM]'),
																				sg.Button 	( 	'Send',
																								key = 'positionerMotorSpeedSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the motor speeds to all the positioners.')
																			],
																			[	sg.Text 	(	'Approach distance',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerApproachDistanceText',
																								size = (25,1)),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-5,5+0.1, 0.1)],
																								initial_value = DEFINES.DEFAULT_APPROACH_DISTANCE,
																								enable_events = True,
																								key = 'positionerApproachDistanceAlphaSpin',
																								size = (7,1),
																								tooltip = 'The alpha approach distance [°].\nBefore going to a target it will go to "target + approach" and only then go to "target". This movement is called the "Approach move"'),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-5,5+0.1, 0.1)],
																								initial_value = DEFINES.DEFAULT_APPROACH_DISTANCE,
																								enable_events = True,
																								key = 'positionerApproachDistanceBetaSpin',
																								size = (7,1),
																								tooltip = 'The beta approach distance [°].\nBefore going to a target it will go to "target + approach" and only then go to "target". This movement is called the "Approach move"'),
																				sg.Button 	( 	'Send',
																								key = 'positionerApproachDistanceSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the approach distances to all the positioners.')
																			],
																			[	sg.Text 	(	'Enable approach move',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerEnableApproachText',
																								size = (27,1)),
																				sg.Checkbox	(	'',
																								default = DEFINES.DEFAULT_ENABLE_APPROACH,
																								enable_events = True,
																								key = 'positionerEnableApproachAlphaCheckbox',
																								size = (5,1),
																								tooltip = 'Enables/Disables the alpha approach move.\nBefore going to a target it will go to "target + approach" and only then go to "target". This movement is called the "Approach move"'),
																				sg.Checkbox	(	'',
																								default = DEFINES.DEFAULT_ENABLE_APPROACH,
																								enable_events = True,
																								key = 'positionerEnableApproachBetaCheckbox',
																								size = (2,1),
																								tooltip = 'Enables/Disables the beta approach move.\nBefore going to a target it will go to "target + approach" and only then go to "target". This movement is called the "Approach move"'),
																				sg.Button 	( 	'Send',
																								key = 'positionerEnableApproachSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the approach move status to all the positioners.')
																			],
																			[	sg.Text 	(	'Shut down motors after move',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerShutDownMotorAfterMoveText',
																								size = (27,1)),
																				sg.Checkbox	(	'',
																								default = DEFINES.DEFAULT_SHUT_DOWN_AFTER_MOVE,
																								enable_events = True,
																								key = 'positionerShutDownMotorAfterMoveCheckbox',
																								size = (12,1),
																								tooltip = 'If set, disables the motor H-bridges after each move.\nThis parameters prevails over the "Low power mode".'),
																				sg.Button 	( 	'Send',
																								key = 'positionerShutDownMotorAfterMoveSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the motor power after move status to all the positioners')
																			],
																			[	sg.Text 	(	'Low power the motors after move',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerLowPowerMotorAfterMoveText',
																								size = (27,1)),
																				sg.Checkbox	(	'',
																								default = DEFINES.DEFAULT_LOW_POWER_AFTER_MOVE,
																								enable_events = True,
																								key = 'positionerLowPowerMotorAfterMoveCheckbox',
																								size = (12,1),
																								tooltip = 'If set, the positioner motors will go in low power mode after each move and use the holding current value.\nElse, it will keep the open loop current (when in open loop) or the cogging current value (when in closed loop).'),
																				sg.Button 	( 	'Send',
																								key = 'positionerLowPowerMotorAfterMoveSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the low motor power after move status to all the positioners')
																			],
																			[	sg.Text 	(	'Current position',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerCurrentPositionText',
																								size = (25,1)),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720+0.1, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerCurrentPositionAlphaSpin',
																								size = (7,1),
																								tooltip = 'The current alpha motor position [°].'),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720+0.1, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerCurrentPositionBetaSpin',
																								size = (7,1),
																								tooltip = 'The current beta motor position [°].'),
																				sg.Button 	( 	'Send',
																								key = 'positionerCurrentPositionSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the current motor positions to all the positioners (not recommended).'),
																				sg.Button 	( 	'Get',
																								key = 'positionerCurrentPositionGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the current motor positions of the first positioner.')
																			],																			
																			[	sg.Text 	(	'Current hardstop offset',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerCurrentHardstopOffsetText',
																								size = (25,1)),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerCurrentHardstopOffsetAlphaSpin',
																								size = (7,1),
																								tooltip = 'The current offset from the alpha hardstop to the 0 position [°].'),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerCurrentHardstopOffsetBetaSpin',
																								size = (7,1),
																								tooltip = 'The current offset from the beta hardstop to the 0 position [°].'),
																				sg.Button 	( 	'Send',
																								key = 'positionerCurrentHardstopOffsetSendButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#90EE90'),
																								tooltip = 'Send the current hardstop offsets to all the positioners (not recommended).'),
																				sg.Button 	( 	'Get',
																								key = 'positionerCurrentHardstopOffsetGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieves the hardstop offsets of the first positioner.')
																			],
																			[	sg.Text 	(	'Movement target',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerMovementTargetText',
																								size = (25,1)),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerMovementTargetAlphaSpin',
																								size = (7,1),
																								tooltip = 'The alpha motor movement target [°].'),
																				sg.Spin 	(	[round(x,1) for x in np.arange(-720,720, 0.1)],
																								initial_value = 0.0,
																								enable_events = True,
																								key = 'positionerMovementTargetBetaSpin',
																								size = (7,1),
																								tooltip = 'The beta motor movement target [°].'),
																				sg.Button 	( 	'Absolute',
																								key = 'positionerMovementTargetAbsoluteButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#9090EE'),
																								tooltip = 'Start an absolute move to the target.'),
																				sg.Button 	( 	'Relative',
																								key = 'positionerMovementTargetRelativeButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Start a relative move from the current position using the target values.')
																			],
																			[	sg.Text 	(	'Current consumption',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerMovementCurrentText',
																								size = (25,1)),
																				sg.Text 	(	'0.0',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								relief=sg.RELIEF_SUNKEN,
																								key = 'positionerMovementCurrentAlphaText',
																								size = (7,1),
																								tooltip = 'The alpha motor current consumption of the first positioner [mA]'),
																				sg.Text 	(	'0.0',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								relief=sg.RELIEF_SUNKEN,
																								key = 'positionerMovementCurrentBetaText',
																								size = (8,1),
																								tooltip = 'The beta motor current consumption of the first positioner [mA]'),
																				sg.Button 	( 	'Get',
																								key = 'positionerMovementCurrentGetButton',
																								enable_events = True, 
																								size = (6,1),
																								button_color = ('black', '#EEEE90'),
																								tooltip = 'Retrieve the motor current consumptions from the first positioner.')																				
																			],
																			[	sg.Text 	(	'Movement time remaining',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerMovementTargetTimeRemainingText1',
																								size = (25,1)),
																				sg.Text 	(	'00.00',
																								justification='right',
																								size = (12,1),
																								relief = sg.RELIEF_SUNKEN,
																								key = 'positionerMovementTargetTimeRemainingText',
																								tooltip = 'The time remaining before movement completion.'),
																				sg.Text 	(	'[s]',
																								font = (DEFINES.GUI_DEFAULT_FONT, 10),
																								justification='left',
																								key = 'positionerMovementTargetTimeRemainingText2',
																								size = (3,1)),
																				sg.Button 	( 	'Abort move',
																								key = 'positionerMovementTargetAbortButton',
																								enable_events = True, 
																								size = (14,1),
																								button_color = ('black', '#EE9090'),
																								tooltip = 'Aborts the current movement operation.')
																			],
																			[	sg.Text('')
																			],
																			[	sg.Text 	(	'No operation',
																								justification='center',
																								size = (60,1),
																								relief = sg.RELIEF_SUNKEN,
																								key = 'positionerCalibrationStatusBarText',
																								tooltip = 'The currently onging operation.')
																			],
																			[	sg.Text('')
																			],
																			[	sg.Button 	( 	'STOP',
																								key = 'positionerStopButton',
																								enable_events = True, 
																								size = (60,2),
																								button_color = ('black', '#EE9090'),
																								tooltip = 'Aborts the current movement operation.')
																			]
																		]
																	, pad = ((0,0),(0,0)))
																]
															]
														, pad = ((0,0),(0,0)))
													]
												]
											, pad = ((0,0),(0,0)))
										]
									]
								, pad = ((0,0),(0,0)))
							]
						]

		self.window = sg.Window('3mm motor manual control', self.layout, grab_anywhere=False, resizable = False)
		
	def init(self):
		self.window.Finalize()
		self.changePositionerFrameState(disable = True)
		self.changeControlFrameState(disable = True)
		self.window.Refresh()

		self.refreshCanUSB()
		if len(self.availableCanComSerials) == 1: #Autoconnect if there is only one device available
			try:
				self.connectCanUSB()
			except errors.CANError:
				self.refreshCanUSB()

	def run(self):
		while True:
			event, values = self.window.Read(timeout = self.GUItimeout)

			if event is None or event == 'GeneralExitButton':
				self.quit()
				return

			elif event == 'refreshCanUSBSerialsButton':
				self.refreshCanUSB()

			elif event == 'connectCanUSBButton':
				self.connectCanUSB()

			elif event == 'disconnectCanUSBButton':
				self.disconnectCanUSB()

			elif event == 'refreshPositionersButton':
				self.refreshPositioners()

			elif event == 'selectPositionersListbox':
				if len(self.window['selectPositionersListbox'].GetListValues()) > 0 and len(list(self.window['selectPositionersListbox'].GetIndexes())) > 0:
					tempPosIDs = self.window['selectPositionersListbox'].GetListValues()
					tempSelectedIDs = list(self.window['selectPositionersListbox'].GetIndexes())
					self.selectedPositionerIDs = [tempPosIDs[i] for i in tempSelectedIDs]
					self.changeControlFrameState(disable = False)
					self.check_status(self.selectedPositionerIDs[0])
				else:
					self.selectedPositionerIDs = []
					self.changeControlFrameState(disable = True)

			elif event == 'bootPositionersButton':
				try:
					for posID in self.selectedPositionerIDs:
						self.comHandle.CAN_write(posID,'boot', [], allowIDInvalidation = False)
					self.bootloaderCountdown = 0
					self.refresh_bootloader_countdown()
							
				except errors.CANError as e:
					user_warning(f'Command was not accepted: {e}')
				except:
					user_warning(f'Command was not accepted.')

			elif event == 'rebootPositionersButton':
				try:
					for posID in self.selectedPositionerIDs:
						self.comHandle.CAN_write(posID,'reboot', [], allowIDInvalidation = False)
					time.sleep(0.5)
					self.check_status(self.selectedPositionerIDs[0])
					
				except errors.CANError:
					pass

			elif event == 'positionerOpenLoopCurrentSendButton':
				self.send_open_loop_current()
				self.get_current_consumption()

			elif event == 'positionerHoldingCurrentSendButton':
				self.send_holding_current()
				self.get_current_consumption()

			elif event == 'positionerMotorSpeedSendButton':
				self.send_motor_speed()

			elif event == 'positionerApproachDistanceSendButton':
				self.send_approach_distance()

			elif event == 'positionerEnableApproachSendButton':
				self.send_enable_approach()

			elif event == 'positionerCurrentPositionSendButton':
				self.send_current_position()

			elif event == 'positionerCurrentPositionGetButton':
				self.get_current_position()

			elif event == 'positionerCurrentHardstopOffsetSendButton':
				self.send_current_hardstop_offset()
				self.get_current_position()

			elif event == 'positionerCurrentHardstopOffsetGetButton':
				self.get_current_hardstop_offset()

			elif event == 'positionerMovementTargetAbsoluteButton':
				self.start_absosute_movement_target()

			elif event == 'positionerMovementTargetRelativeButton':
				self.start_relative_movement_target()

			elif event == 'positionerMovementTargetAbortButton':
				self.stop_trajectory()

			elif event == 'positionerShutDownMotorAfterMoveSendButton':
				self.send_shut_down_motors_after_move()
				self.get_current_consumption()

			elif event == 'positionerLowPowerMotorAfterMoveSendButton':
				self.send_low_power_motors_after_move()
				self.get_current_consumption()

			elif event == 'positionerMovementCurrentGetButton':
				self.get_current_consumption()

			elif event == 'positionerStopButton':
				self.stop_trajectory()

			elif event == 'positionerBLSetAllButton':
				self.set_bootloader_all()

			elif event == 'positionerBLGetAllButton':
				self.get_bootloader_all()

			elif event == 'positionerBL_IDSetButton':
				self.set_bootloader_pos_id()

			elif event == 'positionerBL_IDGetButton':
				self.get_bootloader_pos_id()

			elif event == 'positionerBLReductionRatioSetButton':
				self.set_bootloader_reduction_ratio()

			elif event == 'positionerBLReductionRatioGetButton':
				self.get_bootloader_reduction_ratio()

			elif event == 'positionerBLPolaritySetButton':
				self.set_bootloader_motor_polarity()

			elif event == 'positionerBLPolarityGetButton':
				self.get_bootloader_motor_polarity()

			elif event == 'positionerBLMaxSpeedSetButton':
				self.set_bootloader_max_speed()

			elif event == 'positionerBLMaxSpeedGetButton':
				self.get_bootloader_max_speed()

			elif event == 'positionerBLMaxCurrentSetButton':
				self.set_bootloader_max_current()

			elif event == 'positionerBLMaxCurrentGetButton':
				self.get_bootloader_max_current()

			elif event == 'positionerBLLowRangeLimitSetButton':
				self.set_bootloader_low_range_limit()

			elif event == 'positionerBLLowRangeLimitGetButton':
				self.get_bootloader_low_range_limit()

			elif event == 'positionerBLHighRangeLimitSetButton':
				self.set_bootloader_high_range_limit()

			elif event == 'positionerBLHighRangeLimitGetButton':
				self.get_bootloader_high_range_limit()

			if self.GUItimeout != 0:
				if self.bootloaderCountdown != 0:
					self.refresh_bootloader_countdown()
				if self.positionerMovementTime != 0:
					self.refresh_positioner_movement_timer()

	def set_bootloader_all(self):
		self.set_bootloader_pos_id()
		self.set_bootloader_reduction_ratio()
		self.set_bootloader_motor_polarity()
		self.set_bootloader_max_speed()
		self.set_bootloader_max_current()
		self.set_bootloader_low_range_limit()
		self.set_bootloader_high_range_limit()

	def get_bootloader_all(self):
		self.get_bootloader_pos_id()
		self.get_bootloader_reduction_ratio()
		self.get_bootloader_motor_polarity()
		self.get_bootloader_max_speed()
		self.get_bootloader_max_current()
		self.get_bootloader_low_range_limit()
		self.get_bootloader_high_range_limit()
	
	def set_bootloader_pos_id(self):
		#Only change the first positioner's ID and only if there is not one positioner with the same ID connected
		ID = int(self.window['positionerBL_IDSpin'].Get())
		if ID not in self.availablePositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.POSITIONER_ID, ID, self.selectedPositionerIDs[0])
			self.IDchanged = True
			self.bootloaderCountdown = time.perf_counter()

	def get_bootloader_pos_id(self):
		self.window['positionerBL_IDSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.POSITIONER_ID, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()

#########################################################
	def set_bootloader_reduction_ratio(self):
		valueAlpha = int(self.window['positionerBLReductionRatioAlphaSpin'].Get())
		valueBeta = int(self.window['positionerBLReductionRatioBetaSpin'].Get())

		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_REDUCTION, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_REDUCTION, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_reduction_ratio(self):
		self.window['positionerBLReductionRatioAlphaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_REDUCTION, self.selectedPositionerIDs[0]))
		self.window['positionerBLReductionRatioBetaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_REDUCTION, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
			
	def set_bootloader_motor_polarity(self):
		valueAlpha = self.window['positionerBLPolarityAlphaCombo'].Get()
		valueBeta = self.window['positionerBLPolarityBetaCombo'].Get()
		valueAlpha = self.bootloaderMotorPolarityList.index(valueAlpha)
		valueBeta = self.bootloaderMotorPolarityList.index(valueBeta)

		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_POLARITY, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_POLARITY, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_motor_polarity(self):
		self.window['positionerBLPolarityAlphaCombo'].Update(set_to_index = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_POLARITY, self.selectedPositionerIDs[0]))
		self.window['positionerBLPolarityBetaCombo'].Update(set_to_index = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_POLARITY, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
		
	def set_bootloader_max_speed(self):
		valueAlpha = int(self.window['positionerBLMaxSpeedAlphaSpin'].Get())
		valueBeta = int(self.window['positionerBLMaxSpeedBetaSpin'].Get())

		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_MAX_SPEED, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_MAX_SPEED, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_max_speed(self):
		self.window['positionerBLMaxSpeedAlphaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_MAX_SPEED, self.selectedPositionerIDs[0]))
		self.window['positionerBLMaxSpeedBetaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_MAX_SPEED, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
		
	def set_bootloader_max_current(self):
		valueAlpha = int(self.window['positionerBLMaxCurrentAlphaSpin'].Get())
		valueBeta = int(self.window['positionerBLMaxCurrentBetaSpin'].Get())

		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_MAX_CURRENT, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_MAX_CURRENT, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_max_current(self):
		self.window['positionerBLMaxCurrentAlphaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_MAX_CURRENT, self.selectedPositionerIDs[0]))
		self.window['positionerBLMaxCurrentBetaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_MAX_CURRENT, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
		
	def set_bootloader_low_range_limit(self):
		valueAlpha = int(self.window['positionerBLLowRangeLimitAlphaSpin'].Get())
		valueBeta = int(self.window['positionerBLLowRangeLimitBetaSpin'].Get())
		
		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_LOW_POS_LIMIT, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_LOW_POS_LIMIT, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_low_range_limit(self):
		self.window['positionerBLLowRangeLimitAlphaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_LOW_POS_LIMIT, self.selectedPositionerIDs[0]))
		self.window['positionerBLLowRangeLimitBetaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_LOW_POS_LIMIT, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
		
	def set_bootloader_high_range_limit(self):
		valueAlpha = int(self.window['positionerBLHighRangeLimitAlphaSpin'].Get())
		valueBeta = int(self.window['positionerBLHighRangeLimitBetaSpin'].Get())

		for posID in self.selectedPositionerIDs:
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_HIGH_POS_LIMIT, valueAlpha, posID)
			self.set_bootloader_param(self.comHandle._OPT.BPARAM.BETA_HIGH_POS_LIMIT, valueBeta, posID)
		self.bootloaderCountdown = time.perf_counter()
			
	def get_bootloader_high_range_limit(self):
		self.window['positionerBLHighRangeLimitAlphaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.ALPHA_HIGH_POS_LIMIT, self.selectedPositionerIDs[0]))
		self.window['positionerBLHighRangeLimitBetaSpin'].Update(value = self.get_bootloader_param(self.comHandle._OPT.BPARAM.BETA_HIGH_POS_LIMIT, self.selectedPositionerIDs[0]))
		self.bootloaderCountdown = time.perf_counter()
		
####################################################
	def refreshCanUSB(self):
		try:
			self.availableCanComSerials = self.comHandle.get_all_serial_no()
			self.window['CanUSBSerialsCombo'].Update(values = self.availableCanComSerials)
			
			if len(self.availableCanComSerials) < 1:
				self.window['CanUSBSerialsCombo'].Update(values = [''], value = '')
				self.window['CanUSBSerialsCombo'].Update(values = self.availableCanComSerials)
				self.window['connectCanUSBButton'].Update(disabled = True)
				self.window['disconnectCanUSBButton'].Update(disabled = True)
			else:
				self.window['connectCanUSBButton'].Update(disabled = False)

			if self.currentCanUSBserial is not '' and self.currentCanUSBserial is not None:
				if self.currentCanUSBserial not in self.availableCanComSerials:
					self.comHandle.close()
					self.currentCanUSBserial = ''
					self.window['canUSBStatusText'].Update(value='Disconnected')
		except errors.CANError:
			self.GUItimeout = 0
			self.changePositionerFrameState(disable = True)
			self.changeControlFrameState(disable = True)

	def connectCanUSB(self):
		try:
			self.currentCanUSBserial = self.window['CanUSBSerialsCombo'].Get()
			try:
				self.window['canUSBStatusText'].Update(value='Connecting ...')
				self.window.Refresh()
				self.comHandle.init(self.currentCanUSBserial)
			except errors.CANError:
				self.disconnectCanUSB()
				self.window['connectCanUSBButton'].Update(disabled = True)
				self.window['disconnectCanUSBButton'].Update(disabled = True)
			else:
				self.window['canUSBStatusText'].Update(value=f'{self.currentCanUSBserial} connected')
				self.window['refreshCanUSBSerialsButton'].Update(disabled = True)
				self.window['CanUSBSerialsCombo'].Update(disabled = True)
				self.window['connectCanUSBButton'].Update(disabled = True)
				self.window['disconnectCanUSBButton'].Update(disabled = False)
				self.changePositionerFrameState(disable = False)
				self.refreshPositioners()
		except errors.CANError:
			self.GUItimeout = 0
			self.changePositionerFrameState(disable = True)
			self.changeControlFrameState(disable = True)

	def disconnectCanUSB(self):
		try:
			self.comHandle.close()
			self.currentCanUSBserial = ''
			self.availablePositionerIDs = []
			self.selectedPositionerIDs = []
			self.window['canUSBStatusText'].Update(value='Disconnected')
			self.window['refreshCanUSBSerialsButton'].Update(disabled = False)
			self.window['CanUSBSerialsCombo'].Update(disabled = False)
			self.window['connectCanUSBButton'].Update(disabled = False)
			self.window['disconnectCanUSBButton'].Update(disabled = True)
			self.window['selectPositionersListbox'].Update(values = [])
			self.changePositionerFrameState(disable = True)
			self.changeControlFrameState(disable = True)
			self.bootloaderIsRoot = []
		except errors.CANError:
			self.GUItimeout = 0
			self.changePositionerFrameState(disable = True)
			self.changeControlFrameState(disable = True)

	def refreshPositioners(self):
		try:
			self.availablePositionerIDs = self.comHandle.CAN_write(0,'ask_ID', [], allowIDInvalidation = False)
			self.availablePositionerIDs = [self.availablePositionerIDs[i][0] for i in range(0,len(self.availablePositionerIDs))]
			self.selectedPositionerIDs = self.availablePositionerIDs
			if len(self.availablePositionerIDs) < 1:
				self.window['selectPositionersListbox'].Update(values = [])
				self.changeControlFrameState(disable = True)
			else:
				self.window['selectPositionersListbox'].Update(values = self.availablePositionerIDs, set_to_index = list(range(0,len(self.availablePositionerIDs))))
				self.changeControlFrameState(disable = False)
				self.check_status(self.selectedPositionerIDs[0])
				self.bootloaderIsRoot = []
								
		except errors.CANError:
			self.GUItimeout = 0
			self.changeControlFrameState(disable = True)

	def check_status(self, posID = 0):
		try:
			fwVersion = self.comHandle.CAN_write(posID,'get_firmware_version', [], allowIDInvalidation = False)
			if fwVersion is not None and fwVersion is not [] and fwVersion[0] is not [] and fwVersion[0][0] is not None:
				if fwVersion[0][0].split('.')[1] == DEFINES.POS_BOOTLOADER_FIRMWARE_ID:
					bstatus = self.comHandle.CAN_write(0,'get_bootloader_status', [], allowIDInvalidation = False)
					if bstatus is not None and bstatus is not [] and bstatus[0] is not []:						
						self.change_bootloader_control_frame_state(disable=False)
						self.change_normal_operation_control_frame_state(disable=True)
						self.GUItimeout = 10
						if self.bootloaderCountdown == 0:
							self.get_bootloader_all()
						self.bootloaderCountdown = time.perf_counter()
				else:
					self.bootloaderCountdown = 0
					status = self.comHandle.CAN_write(0,'status_request', [], allowIDInvalidation = False)
					if status is not None and status is not [] and status[0] is not []:
						self.change_bootloader_control_frame_state(disable=True)
						if self.positionerMovementTime == 0:
							self.change_normal_operation_control_frame_state(disable=False)
							self.init_positioners()
						self.get_current_position()
						self.get_current_hardstop_offset()
						self.get_current_consumption()
						self.update_positioner_config_from_status(status[0][0])

		except errors.CANError:
			self.GUItimeout = 0
			self.changeControlFrameState(disable = True)

	def send_status(self):
		try:
			fwVersion = self.comHandle.CAN_write(self.selectedPositionerIDs[0],'get_firmware_version', [], allowIDInvalidation = False)
			if fwVersion is not None and fwVersion is not [] and fwVersion[0] is not []:
				if fwVersion[0][0].split('.')[1] == DEFINES.POS_BOOTLOADER_FIRMWARE_ID:
					pass
				else:
					regSet = 	self.comHandle._OPT.STREG.COLLISION_DETECT_ALPHA_DISABLE +\
								self.comHandle._OPT.STREG.COLLISION_DETECT_BETA_DISABLE +\
								self.comHandle._OPT.STREG.MOTOR_ALPHA_CALIBRATED +\
								self.comHandle._OPT.STREG.MOTOR_BETA_CALIBRATED +\
								self.comHandle._OPT.STREG.DATUM_ALPHA_CALIBRATED +\
								self.comHandle._OPT.STREG.DATUM_BETA_CALIBRATED +\
								self.comHandle._OPT.STREG.DATUM_ALPHA_INITIALIZED +\
								self.comHandle._OPT.STREG.DATUM_BETA_INITIALIZED +\
								self.comHandle._OPT.STREG.HALL_ALPHA_DISABLE +\
								self.comHandle._OPT.STREG.HALL_BETA_DISABLE +\
								self.comHandle._OPT.STREG.COGGING_ALPHA_CALIBRATED +\
								self.comHandle._OPT.STREG.COGGING_BETA_CALIBRATED +\
								self.comHandle._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_ALPHA +\
								self.comHandle._OPT.STREG.PRECISE_MOVE_IN_OPEN_LOOP_BETA +\
								self.comHandle._OPT.STREG.SWITCH_OFF_HALL_AFTER_MOVE

					regClear = 	self.comHandle._OPT.STREG.COLLISION_ALPHA +\
								self.comHandle._OPT.STREG.COLLISION_BETA +\
								self.comHandle._OPT.STREG.CLOSED_LOOP_ALPHA +\
								self.comHandle._OPT.STREG.CLOSED_LOOP_BETA

					if self.window['positionerEnableApproachAlphaCheckbox'].Get():
						regSet+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_ALPHA
					else:
						regClear+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_ALPHA
					if self.window['positionerEnableApproachBetaCheckbox'].Get():
						regSet+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_BETA
					else:
						regClear+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_BETA
					if self.window['positionerShutDownMotorAfterMoveCheckbox'].Get():
						regSet+=self.comHandle._OPT.STREG.SWITCH_OFF_AFTER_MOVE
					else:
						regClear+=self.comHandle._OPT.STREG.SWITCH_OFF_AFTER_MOVE
					if self.window['positionerLowPowerMotorAfterMoveCheckbox'].Get():
						regSet+=self.comHandle._OPT.STREG.LOW_POWER_AFTER_MOVE
					else:
						regClear+=self.comHandle._OPT.STREG.LOW_POWER_AFTER_MOVE

					for posID in self.selectedPositionerIDs:
						self.comHandle.send_full_status(posID, regSet = regSet, regClear = regClear, allowIDInvalidation = False)
					
		except errors.CANError:
			self.changeControlFrameState(disable = True)

	def init_positioners(self):
		self.bootloaderIsRoot = []
		self.send_open_loop_current()
		self.send_holding_current()
		self.send_motor_speed()
		self.send_approach_distance()
		self.send_status()
		self.get_current_position()
		self.get_current_hardstop_offset()
		self.get_current_consumption()

	def refresh_bootloader_countdown(self):
		tRemaining = self.bootloaderCountdown + DEFINES.GUI_BOOTLOADER_WATCHDOG - time.perf_counter()
		if tRemaining < 0:
			tRemaining = 0.0
			self.GUItimeout = 0
			self.bootloaderCountdown = 0
			self.bootloaderIsRoot = []
			time.sleep(1)
			if self.IDchanged:
				time.sleep(1)
				self.refreshPositioners()
				self.IDchanged = False
			if len(self.selectedPositionerIDs)>0:
				self.check_status(self.selectedPositionerIDs[0])
		elif self.window['positionerBootloaderTimerAutorefreshCheckbox'].Get():# and tRemaining < DEFINES.GUI_BOOTLOADER_WATCHDOG/2:
			for posID in self.selectedPositionerIDs:
				self.check_status(posID)

		self.window['positionerBootloaderTimerText'].Update(value = f'{max(tRemaining,0):02.2f}')

	def refresh_positioner_movement_timer(self):
		tRemaining = self.positionerMovementTime - time.perf_counter()

		self.get_current_position()
		self.get_current_hardstop_offset()
		self.get_current_consumption()

		if tRemaining < 0:
			tRemaining = 0.0
			self.GUItimeout = 0
			self.positionerMovementTime = 0
			self.change_normal_operation_control_frame_state(disable = False)
			self.window['positionerCalibrationStatusBarText'].Update(value = 'No operation')
			
		self.window['positionerMovementTargetTimeRemainingText'].Update(value = f'{tRemaining:03.2f}')

	def send_open_loop_current(self):
		try:
			data = {'currentAlpha': int(self.window['positionerOpenLoopCurrentAlphaSpin'].Get()),
					'currentBeta': int(self.window['positionerOpenLoopCurrentBetaSpin'].Get())}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_openloop_current', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_holding_current(self):
		try:
			data = {'holdingCurrentAlpha': int(self.window['positionerHoldingCurrentAlphaSpin'].Get()),
					'holdingCurrentBeta': int(self.window['positionerHoldingCurrentBetaSpin'].Get())}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_holding_current', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_motor_speed(self):
		try:
			data = {'speedAlpha': int(self.window['positionerMotorSpeedAlphaSpin'].Get()),
					'speedBeta': int(self.window['positionerMotorSpeedBetaSpin'].Get())}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_speed', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_approach_distance(self):
		try:
			data = {'approachAlpha': int(float(self.window['positionerApproachDistanceAlphaSpin'].Get())*(2**30)/360),
					'approachBeta': int(float(self.window['positionerApproachDistanceBetaSpin'].Get())*(2**30)/360)}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_approach', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_enable_approach(self):
		try:
			dataSet = 0
			dataClear = 0
			if self.window['positionerEnableApproachAlphaCheckbox'].Get():
				dataSet+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_ALPHA
			else:
				dataClear+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_ALPHA
			if self.window['positionerEnableApproachBetaCheckbox'].Get():
				dataSet+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_BETA
			else:
				dataClear+=self.comHandle._OPT.STREG.PRECISE_POSITIONING_BETA

			for posID in self.selectedPositionerIDs:
				self.comHandle.send_full_status(posID, regSet = dataSet, regClear = dataClear, allowIDInvalidation = False)

		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_shut_down_motors_after_move(self):
		try:
			dataSet = 0
			dataClear = 0
			if self.window['positionerShutDownMotorAfterMoveCheckbox'].Get():
				dataSet+=self.comHandle._OPT.STREG.SWITCH_OFF_AFTER_MOVE
			else:
				dataClear+=self.comHandle._OPT.STREG.SWITCH_OFF_AFTER_MOVE
			
			for posID in self.selectedPositionerIDs:
				self.comHandle.send_full_status(posID, regSet = dataSet, regClear = dataClear, allowIDInvalidation = False)

		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_low_power_motors_after_move(self):
		try:
			dataSet = 0
			dataClear = 0
			if self.window['positionerLowPowerMotorAfterMoveCheckbox'].Get():
				dataSet+=self.comHandle._OPT.STREG.LOW_POWER_AFTER_MOVE
			else:
				dataClear+=self.comHandle._OPT.STREG.LOW_POWER_AFTER_MOVE
			
			for posID in self.selectedPositionerIDs:
				self.comHandle.send_full_status(posID, regSet = dataSet, regClear = dataClear, allowIDInvalidation = False)

		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def send_current_position(self):
		try:
			data = {'currentAlphaPos': int(float(self.window['positionerCurrentPositionAlphaSpin'].Get())/360*(2**30)),
					'currentBetaPos': int(float(self.window['positionerCurrentPositionBetaSpin'].Get())/360*(2**30))}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_position', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def get_current_position(self):
		try:
			currentPos = self.comHandle.CAN_write(self.selectedPositionerIDs[0],'get_position', [], allowIDInvalidation = False)
			self.window['positionerCurrentPositionAlphaSpin'].Update(value = round(currentPos[0][0]*360/(2**30),2))
			self.window['positionerCurrentPositionBetaSpin'].Update(value = round(currentPos[0][1]*360/(2**30),2))
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted.')

	def get_current_consumption(self):
		try:
			currentCons = self.comHandle.CAN_write(self.selectedPositionerIDs[0],'get_current_consumption', [], allowIDInvalidation = False)
			self.window['positionerMovementCurrentAlphaText'].Update(value = round(currentCons[0][0],2))
			self.window['positionerMovementCurrentBetaText'].Update(value = round(currentCons[0][1],2))
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted.')

	def send_current_hardstop_offset(self):
		try:
			data = {'alphaOffset': int(float(self.window['positionerCurrentHardstopOffsetAlphaSpin'].Get())/360*(2**30)),
					'betaOffset': int(float(self.window['positionerCurrentHardstopOffsetBetaSpin'].Get())/360*(2**30))}
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'set_offset', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def get_current_hardstop_offset(self):
		try:
			currentPos = self.comHandle.CAN_write(self.selectedPositionerIDs[0],'get_offset', [], allowIDInvalidation = False)
			self.window['positionerCurrentHardstopOffsetAlphaSpin'].Update(value = round(currentPos[0][0]*360/(2**30),2))
			self.window['positionerCurrentHardstopOffsetBetaSpin'].Update(value = round(currentPos[0][1]*360/(2**30),2))
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted.')

	def start_absosute_movement_target(self):
		try:
			maxTime = 0
			data = {'R1Steps': int(float(self.window['positionerMovementTargetAlphaSpin'].Get())/360*(2**30)),
					'R2Steps': int(float(self.window['positionerMovementTargetBetaSpin'].Get())/360*(2**30))}
			for posID in self.selectedPositionerIDs:
				tempTime = self.comHandle.CAN_write(posID,'goto_position_absolute', data, allowIDInvalidation = False)
				maxTime = max(maxTime, max(tempTime[0]))

			self.change_normal_operation_control_frame_state(disable = True)
			self.reenable_control_frame_movement_fields()
			self.window['positionerCalibrationStatusBarText'].Update(value = 'Absolute move in progress', text_color = 'white') 

			self.GUItimeout = 10
			self.positionerMovementTime = maxTime+time.perf_counter()

		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')


	def start_relative_movement_target(self):
		try:
			maxTime = 0
			data = {'R1Steps': int(float(self.window['positionerMovementTargetAlphaSpin'].Get())/360*(2**30)),
					'R2Steps': int(float(self.window['positionerMovementTargetBetaSpin'].Get())/360*(2**30))}
			for posID in self.selectedPositionerIDs:
				tempTime = self.comHandle.CAN_write(posID,'goto_position_relative', data, allowIDInvalidation = False)
				maxTime = max(maxTime, max(tempTime[0]))

			self.change_normal_operation_control_frame_state(disable = True)
			self.reenable_control_frame_movement_fields()
			self.window['positionerCalibrationStatusBarText'].Update(value = 'Relative move in progress', text_color = 'white')

			self.GUItimeout = 10
			self.positionerMovementTime = maxTime+time.perf_counter()

		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted. Check data')

	def get_bootloader_param(self, parameter, posID):
		try:
			data = {'bootloaderParameter': parameter}
			response = self.comHandle.CAN_write(posID,'get_bootloader_parameter', data, allowIDInvalidation = False)
			if response is not  None and response is not [] and response[0] is not []:
				return response[0][0]
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted')
		return None

	def set_bootloader_param(self, parameter, value, posID):
		try:
			if posID not in self.bootloaderIsRoot:
				self.comHandle.CAN_write(posID,'get_root_access', [], allowIDInvalidation = False)
				self.bootloaderIsRoot.append(posID)
			data = {'bootloaderParameter': parameter,
					'bootloaderParameterValue': value}
			response = self.comHandle.CAN_write(posID,'set_bootloader_parameter', data, allowIDInvalidation = False)
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted')

	def stop_trajectory(self):
		try:
			for posID in self.selectedPositionerIDs:
				self.comHandle.CAN_write(posID,'stop_trajectory', [], allowIDInvalidation = False)
			self.positionerMovementTime = 0
			self.refresh_positioner_movement_timer()
		except errors.CANError as e:
			user_warning(f'Command was not accepted: {e}')
		except:
			user_warning(f'Command was not accepted.')

	def update_positioner_config_from_status(self,status):
		if status&self.comHandle._OPT.STREG.SWITCH_OFF_AFTER_MOVE:
			self.window['positionerShutDownMotorAfterMoveCheckbox'].Update(value = True)
		else:
			self.window['positionerShutDownMotorAfterMoveCheckbox'].Update(value = False)
		if status&self.comHandle._OPT.STREG.LOW_POWER_AFTER_MOVE:
			self.window['positionerLowPowerMotorAfterMoveCheckbox'].Update(value = True)
		else:
			self.window['positionerLowPowerMotorAfterMoveCheckbox'].Update(value = False)
		if status&self.comHandle._OPT.STREG.PRECISE_POSITIONING_ALPHA:
			self.window['positionerEnableApproachAlphaCheckbox'].Update(value = True)
		else:
			self.window['positionerEnableApproachAlphaCheckbox'].Update(value = False)
		if status&self.comHandle._OPT.STREG.PRECISE_POSITIONING_BETA:
			self.window['positionerEnableApproachBetaCheckbox'].Update(value = True)
		else:
			self.window['positionerEnableApproachBetaCheckbox'].Update(value = False)
		
	def changePositionerFrameState(self,disable):
		self.window['refreshPositionersButton'].Update(disabled = disable)
		self.window['selectPositionersListbox'].Update(disabled = disable)

	def change_bootloader_control_frame_state(self,disable):
		if disable:
			textColor = 'grey'
		else:
			textColor = 'white'

		self.window['positionerBLGeneralText'].Update(text_color = textColor)
		self.window['positionerBLAlphaText'].Update(text_color = textColor)
		self.window['positionerBLBetaText'].Update(text_color = textColor)
		self.window['positionerBootloaderTimerText'].Update(text_color = textColor)
		self.window['positionerBootloaderTimerText1'].Update(text_color = textColor)
		self.window['positionerBootloaderTimerText2'].Update(text_color = textColor)
		self.window['positionerBL_IDText'].Update(text_color = textColor)
		self.window['positionerBLReductionRatioText'].Update(text_color = textColor)
		self.window['positionerBLPolarityText'].Update(text_color = textColor)
		self.window['positionerBLMaxSpeedText'].Update(text_color = textColor)
		self.window['positionerBLMaxCurrentText'].Update(text_color = textColor)
		self.window['positionerBLLowRangeLimitText'].Update(text_color = textColor)
		self.window['positionerBLHighRangeLimitText'].Update(text_color = textColor)

		self.window['bootPositionersButton'].Update(disabled = disable)
		self.window['positionerBootloaderTimerAutorefreshCheckbox'].Update(disabled = disable)
		self.window['positionerBLSetAllButton'].Update(disabled = disable)
		self.window['positionerBLGetAllButton'].Update(disabled = disable)
		self.window['positionerBL_IDSpin'].Update(disabled = disable)
		self.window['positionerBL_IDSetButton'].Update(disabled = disable)
		self.window['positionerBL_IDGetButton'].Update(disabled = disable)
		self.window['positionerBLReductionRatioAlphaSpin'].Update(disabled = disable)
		self.window['positionerBLReductionRatioBetaSpin'].Update(disabled = disable)
		self.window['positionerBLReductionRatioSetButton'].Update(disabled = disable)
		self.window['positionerBLReductionRatioGetButton'].Update(disabled = disable)
		self.window['positionerBLPolarityAlphaCombo'].Update(disabled = disable)
		self.window['positionerBLPolarityBetaCombo'].Update(disabled = disable)
		self.window['positionerBLPolaritySetButton'].Update(disabled = disable)
		self.window['positionerBLPolarityGetButton'].Update(disabled = disable)
		self.window['positionerBLMaxSpeedAlphaSpin'].Update(disabled = disable)
		self.window['positionerBLMaxSpeedBetaSpin'].Update(disabled = disable)
		self.window['positionerBLMaxSpeedSetButton'].Update(disabled = disable)
		self.window['positionerBLMaxSpeedGetButton'].Update(disabled = disable)
		self.window['positionerBLMaxCurrentAlphaSpin'].Update(disabled = disable)
		self.window['positionerBLMaxCurrentBetaSpin'].Update(disabled = disable)
		self.window['positionerBLMaxCurrentSetButton'].Update(disabled = disable)
		self.window['positionerBLMaxCurrentGetButton'].Update(disabled = disable)
		self.window['positionerBLLowRangeLimitAlphaSpin'].Update(disabled = disable)
		self.window['positionerBLLowRangeLimitBetaSpin'].Update(disabled = disable)
		self.window['positionerBLLowRangeLimitSetButton'].Update(disabled = disable)
		self.window['positionerBLLowRangeLimitGetButton'].Update(disabled = disable)
		self.window['positionerBLHighRangeLimitAlphaSpin'].Update(disabled = disable)
		self.window['positionerBLHighRangeLimitBetaSpin'].Update(disabled = disable)
		self.window['positionerBLHighRangeLimitSetButton'].Update(disabled = disable)
		self.window['positionerBLHighRangeLimitGetButton'].Update(disabled = disable)

	def change_normal_operation_control_frame_state(self,disable):
		if disable:
			textColor = 'grey'
		else:
			textColor = 'white'

		self.window['positionerNormalAlphaText'].Update(text_color = textColor)
		self.window['positionerNormalBetaText'].Update(text_color = textColor)
		self.window['positionerOpenLoopCurrentText'].Update(text_color = textColor)
		self.window['positionerHoldingCurrentText'].Update(text_color = textColor)
		self.window['positionerMotorSpeedText'].Update(text_color = textColor)
		self.window['positionerApproachDistanceText'].Update(text_color = textColor)
		self.window['positionerEnableApproachText'].Update(text_color = textColor)
		self.window['positionerCurrentPositionText'].Update(text_color = textColor)
		self.window['positionerCurrentHardstopOffsetText'].Update(text_color = textColor)
		self.window['positionerMovementTargetText'].Update(text_color = textColor)
		self.window['positionerMovementTargetTimeRemainingText1'].Update(text_color = textColor)
		self.window['positionerMovementTargetTimeRemainingText'].Update(text_color = textColor)
		self.window['positionerMovementTargetTimeRemainingText2'].Update(text_color = textColor)
		self.window['positionerShutDownMotorAfterMoveText'].Update(text_color = textColor)
		self.window['positionerLowPowerMotorAfterMoveText'].Update(text_color = textColor)
		self.window['positionerCalibrationStatusBarText'].Update(text_color = textColor)
		self.window['positionerMovementCurrentText'].Update(text_color = textColor)
		self.window['positionerMovementCurrentAlphaText'].Update(text_color = textColor)
		self.window['positionerMovementCurrentBetaText'].Update(text_color = textColor)

		self.window['positionerShutDownMotorAfterMoveCheckbox'].Update(disabled = disable)
		self.window['positionerShutDownMotorAfterMoveSendButton'].Update(disabled = disable)
		self.window['positionerLowPowerMotorAfterMoveCheckbox'].Update(disabled = disable)
		self.window['positionerLowPowerMotorAfterMoveSendButton'].Update(disabled = disable)
		self.window['positionerOpenLoopCurrentAlphaSpin'].Update(disabled = disable)
		self.window['positionerOpenLoopCurrentBetaSpin'].Update(disabled = disable)
		self.window['positionerOpenLoopCurrentSendButton'].Update(disabled = disable)
		self.window['positionerHoldingCurrentAlphaSpin'].Update(disabled = disable)
		self.window['positionerHoldingCurrentBetaSpin'].Update(disabled = disable)
		self.window['positionerHoldingCurrentSendButton'].Update(disabled = disable)
		self.window['positionerMotorSpeedAlphaSpin'].Update(disabled = disable)
		self.window['positionerMotorSpeedBetaSpin'].Update(disabled = disable)
		self.window['positionerMotorSpeedSendButton'].Update(disabled = disable)
		self.window['positionerApproachDistanceAlphaSpin'].Update(disabled = disable)
		self.window['positionerApproachDistanceBetaSpin'].Update(disabled = disable)
		self.window['positionerApproachDistanceSendButton'].Update(disabled = disable)
		self.window['positionerEnableApproachAlphaCheckbox'].Update(disabled = disable)
		self.window['positionerEnableApproachBetaCheckbox'].Update(disabled = disable)
		self.window['positionerEnableApproachSendButton'].Update(disabled = disable)
		self.window['positionerCurrentPositionAlphaSpin'].Update(disabled = disable)
		self.window['positionerCurrentPositionBetaSpin'].Update(disabled = disable)
		self.window['positionerCurrentPositionSendButton'].Update(disabled = disable)
		self.window['positionerCurrentPositionGetButton'].Update(disabled = disable)
		self.window['positionerCurrentHardstopOffsetAlphaSpin'].Update(disabled = disable)
		self.window['positionerCurrentHardstopOffsetBetaSpin'].Update(disabled = disable)
		self.window['positionerCurrentHardstopOffsetSendButton'].Update(disabled = disable)
		self.window['positionerCurrentHardstopOffsetGetButton'].Update(disabled = disable)
		self.window['positionerMovementTargetAlphaSpin'].Update(disabled = disable)
		self.window['positionerMovementTargetBetaSpin'].Update(disabled = disable)
		self.window['positionerMovementTargetAbsoluteButton'].Update(disabled = disable)
		self.window['positionerMovementTargetRelativeButton'].Update(disabled = disable)
		self.window['positionerMovementTargetAbortButton'].Update(disabled = disable)
		self.window['positionerStopButton'].Update(disabled = disable)
		self.window['positionerMovementCurrentGetButton'].Update(disabled = disable)

	def changeControlFrameState(self,disable):
		self.change_bootloader_control_frame_state(disable)
		self.change_normal_operation_control_frame_state(disable)
		self.window['rebootPositionersButton'].Update(disabled = disable)
		
	def reenable_control_frame_movement_fields(self):
		self.window['positionerCurrentPositionAlphaSpin'].Update(disabled = False)
		self.window['positionerCurrentPositionBetaSpin'].Update(disabled = False)
		self.window['positionerMovementCurrentAlphaText'].Update(text_color = 'white')
		self.window['positionerMovementCurrentBetaText'].Update(text_color = 'white')
		self.window['positionerMovementTargetTimeRemainingText1'].Update(text_color = 'white')
		self.window['positionerMovementTargetTimeRemainingText'].Update(text_color = 'white')
		self.window['positionerMovementTargetTimeRemainingText2'].Update(text_color = 'white')
		self.window['positionerCurrentPositionText'].Update(text_color = 'white')
		self.window['positionerMovementCurrentText'].Update(text_color = 'white')
		self.window['positionerStopButton'].Update(disabled = False)
		self.window['positionerMovementTargetAbortButton'].Update(disabled = False)

	def quit(self):
		self.window.Close()

def user_warning(text):
		sg.ChangeLookAndFeel('SystemDefault') 
		popup = sg.Window('Warning', 
							[
								[ 	sg.Text 	(	text
												)
								],
								[	sg.Button 	(	'Ok',
													size = (18,1),
													button_color = ('black', '#90EE90'), 
													enable_events = True,
													key = 'Confirmation_OK_Button')
								]
							], grab_anywhere=True, resizable = False, no_titlebar = True, keep_on_top = True)

		popup.Finalize()

		while True:
			event, values = popup.Read()
			if event == 'Confirmation_OK_Button':
				popup.close()
				return

def error_popup(text):
	sg.ChangeLookAndFeel('SystemDefault') 
	popup = sg.Window('Critical error', 
						[
							[ 	sg.Text 	(	text
											)
							],
							[	sg.Button 	(	'Ok',
												size = (18,1),
												button_color = ('black', '#90EE90'), 
												enable_events = True,
												key = 'Confirmation_OK_Button')
							]
						], grab_anywhere=True, resizable = False, no_titlebar = True, keep_on_top = True)

	popup.Finalize()

	while True:
		event, values = popup.Read()
		if event == 'Confirmation_OK_Button':
			popup.close()
			return

def main():
	
	try:
		my_gui = ManualControlWindow()
		my_gui.init()
		my_gui.run()
		del my_gui

	except:
		error_popup(f'CRITICAL : A fatal error occured !\n\n{traceback.format_exc()}')

if __name__ == '__main__':
	main()