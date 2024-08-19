from monitors import ConvertToPdfMonitor, IsSearchable,Split_pdf,EngineMonitor


#monitors = [ConvertToPdfMonitor(),IsSearchable(),split_pdf(),EngineMonitor()]
monitors = [EngineMonitor("RHYTHM")]

for monitor in monitors:
    monitor.check_pulses()
    print(monitor.pulse_errors)
