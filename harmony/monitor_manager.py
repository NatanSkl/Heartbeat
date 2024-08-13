from monitors import ConvertToPdfMonitor, IsSearchable,Split_pdf


#monitors = [ConvertToPdfMonitor(),IsSearchable(),split_pdf()]
monitors = [Split_pdf()]

for monitor in monitors:
    monitor.check_pulses()
    print(monitor.pulse_errors)
