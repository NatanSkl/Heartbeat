from monitors import (ConvertToPdfMonitor, IsSearchable,Split_pdf,EngineMonitor,DocumentAiMonitor,AzureDiMonitor
,RhythemMonitor,CombineMonitor,CombinePdfMonitor,CombineLsdMonitor)


monitors = [ConvertToPdfMonitor(),IsSearchable(),Split_pdf(),DocumentAiMonitor(),AzureDiMonitor()
    ,RhythemMonitor(),CombinePdfMonitor(),CombineLsdMonitor]


for monitor in monitors:
    monitor.check_pulses()
    print(monitor.pulse_errors)
