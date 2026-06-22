_______________________________________________________________ 분배예정
# 상단일수록 작업수행 우선순위 높음

🔳 fixing: SSID tracer terminal pane UI requests
    replace Windows Terminal layout so 4 panes have equal width/area
    change DETECTED SSID color to white
    change RESULT section color to white
    keep only FAILED/PASSED text red/green in RESULT section
    make Config pane selectable as interactive fzf-like selector via ensure_value_completed
    selector options: config_26_ssids, config_55_ssids, config_2_ssids_as_e8e4_for_mesh_networking, config_2_ssids_as_eb98
    selected config must apply to result/detected/statistics/config panes
    merge Config pane Expected 5G and Expected 2.4G into Intended({ssid cnt})
    merge Config pane Planned band sections into Planned({ssid cnt})
    merge Config pane Ignored band sections into Ignored({ssid cnt})
    make STATISTICS pane simple
