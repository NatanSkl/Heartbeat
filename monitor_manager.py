from harmony.monitors import (ConvertToPdfMonitor, IsSearchable, Split_pdf, DocumentAiMonitor, AzureDiMonitor
                    , RhythemMonitor, CombinePdfMonitor, CombineLsdMonitor)


monitors = [ConvertToPdfMonitor(),IsSearchable(),Split_pdf(),DocumentAiMonitor(),AzureDiMonitor()
    ,RhythemMonitor(),CombinePdfMonitor(),CombineLsdMonitor()]


#for env in ["test", "prod"]:
for monitor in monitors:
    monitor.check_pulses("test")
    print(monitor.pulse_errors)
