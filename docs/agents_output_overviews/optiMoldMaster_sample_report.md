
**Demo**: [🔗View OptiMoldIQ Dashboard (Live Demo - CodeSandbox.io)](https://4w5jm3.csb.app/)

```
================================================================================
GENERATED DATA PROCESSING REPORTS
================================================================================

• OVERALL_STATUS: success
• COLLECTOR_RESULT:
  • AGENT_ID: DataCollector
  • TIMESTAMP: 2025-08-23T19:13:40.564205
  • STATUS: success
  • SUMMARY:
    • TOTAL_DATASETS: 2
    • SUCCESSFUL: 2
    • FAILED: 0
    • WARNINGS: 0
  • DETAILS:
      • DATA_TYPE: productRecords
      • STATUS: success
      • FILES_PROCESSED: 3
      • FILES_SUCCESSFUL: 3
      • FILES_FAILED: 0
      • FAILED_FILES: 
      • RECORDS_PROCESSED: 2134
      • OUTPUT_FILE: tests/shared_db/dynamicDatabase/productRecords.parquet
      • FILE_SIZE_MB: 0.06450557708740234
      • DATA_UPDATED: True
      • ERROR_TYPE: data_processing_error
      • RECOVERY_ACTIONS: 
      • WARNINGS: 
      • DATA_TYPE: purchaseOrders
      • STATUS: success
      • FILES_PROCESSED: 7
      • FILES_SUCCESSFUL: 7
      • FILES_FAILED: 0
      • FAILED_FILES: 
      • RECORDS_PROCESSED: 190
      • OUTPUT_FILE: tests/shared_db/dynamicDatabase/purchaseOrders.parquet
      • FILE_SIZE_MB: 0.016204833984375
      • DATA_UPDATED: True
      • ERROR_TYPE: data_processing_error
      • RECOVERY_ACTIONS: 
      • WARNINGS: 
  • HEALING_ACTIONS: 
  • TRIGGER_AGENTS: DataLoader
  • METADATA:
    • PROCESSING_DURATION: None
    • DISK_USAGE:
      • OUTPUT_DIRECTORY_MB: 0.08071041107177734
      • AVAILABLE_SPACE_MB: 70352.6015625
• LOADER_RESULT:
  • AGENT_ID: DataLoader
  • TIMESTAMP: 2025-08-23T19:13:41.915036
  • STATUS: success
  • SUMMARY:
    • TOTAL_DATABASES: 8
    • SUCCESSFUL: 8
    • FAILED: 0
    • WARNINGS: 0
    • CHANGED_FILES: 8
    • FILES_SAVED: 1
  • DETAILS:
      • DATABASE_NAME: productRecords
      • DATABASE_TYPE: dynamicDB
      • STATUS: success
      • RECORDS_PROCESSED: 2134
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 2134 rows × 32 columns
           (showing first/last 5 rows, showing first 10 columns)
        
        ┌─────────────────────┬──────────────┬───────────┬─────────────┬───────────┬──────────────────────────────┬──────────────┬─────────────┬────────────────┬───────────┐
        │      recordDate     │ workingShift │ machineNo │ machineCode │  itemCode │           itemName           │ colorChanged │ moldChanged │ machineChanged │   poNote  │
        ├─────────────────────┼──────────────┼───────────┼─────────────┼───────────┼──────────────────────────────┼──────────────┼─────────────┼────────────────┼───────────┤
        │ 2018-11-01 00:00:00 │ 1            │ NO.01     │ MD50S-000   │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │              │             │                │ IM1811001 │
        │ 2018-11-01 00:00:00 │ 1            │ NO.02     │ MD50S-001   │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY      │              │             │                │ IM1811015 │
        │ 2018-11-01 00:00:00 │ 1            │ NO.03     │ EC50ST-000  │ 262001M   │ CT-PXN-CORE-4.2              │              │             │                │ IM1811044 │
        │ 2018-11-01 00:00:00 │ 1            │ NO.04     │ J100ADS-000 │ 24720475M │ CT-YCN-BASE-WHITE            │              │             │                │ IM1811025 │
        │ 2018-11-01 00:00:00 │ 1            │ NO.05     │ J100ADS-001 │ 280503M   │ CT-PS-SMALL-REEL-5.0MM-RED   │              │             │                │ IM1811048 │
        │ 2019-01-31 00:00:00 │ 3            │ NO.07     │ MD100S-001  │ 24720319M │ CT-CAX-UPPER-CASE-PINK       │              │             │                │ IM1901026 │
        │ 2019-01-31 00:00:00 │ 3            │ NO.08     │ MD130S-000  │ 24720323M │ CT-CAX-LOWER-CASE-PINK       │              │             │                │ IM1901028 │
        │ 2019-01-31 00:00:00 │ 3            │ NO.09     │ MD130S-001  │ 24720327M │ CT-CAX-BASE-COVER            │              │             │                │ IM1901032 │
        │ 2019-01-31 00:00:00 │ 3            │ NO.10     │ CNS50-000   │ 281709M   │ CT-PS-SPACER                 │              │             │                │ IM1901060 │
        │ 2019-01-31 00:00:00 │ 3            │ NO.11     │ CNS50-001   │ 260501M1  │ CT-PXN-HEAD-COVER-4.2MM      │              │             │                │ IM1901044 │
        └─────────────────────┴──────────────┴───────────┴─────────────┴───────────┴──────────────────────────────┴──────────────┴─────────────┴────────────────┴───────────┘
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: purchaseOrders
      • DATABASE_TYPE: dynamicDB
      • STATUS: success
      • RECORDS_PROCESSED: 190
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 190 rows × 15 columns
           (showing first/last 5 rows, showing first 10 columns)
        
        ┌─────────────────────┬───────────┬─────────────────────┬───────────┬──────────────────────────────┬──────────────┬──────────────────┬────────────────────┬──────────────────────┬──────────────────────┐
        │    poReceivedDate   │    poNo   │        poETA        │  itemCode │           itemName           │ itemQuantity │ plasticResinCode │    plasticResin    │ plasticResinQuantity │ colorMasterbatchCode │
        ├─────────────────────┼───────────┼─────────────────────┼───────────┼──────────────────────────────┼──────────────┼──────────────────┼────────────────────┼──────────────────────┼──────────────────────┤
        │ 2018-10-20 00:00:00 │ IM1811001 │ 2018-11-05 00:00:00 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 280000       │ 10045            │ ABS-PA-758-T.NL    │ 606.0                │ 10190                │
        │ 2018-10-20 00:00:00 │ IM1811008 │ 2018-11-05 00:00:00 │ 24720318M │ CT-CAX-UPPER-CASE-BLUE       │ 30000        │ 10048            │ PC122-T.NL         │ 206.0                │ 10115                │
        │ 2018-10-20 00:00:00 │ IM1811015 │ 2018-11-05 00:00:00 │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY      │ 15000        │ 9915740199       │ POM-RE-F20-T.NL    │ 22.0                 │ 10106                │
        │ 2018-10-20 00:00:00 │ IM1811016 │ 2018-11-05 00:00:00 │ 24720326M │ CT-CAX-CARTRIDGE-BASE        │ 270000       │ 9915540700       │ PS-RE-GPCD40T-T.NL │ 609.0                │                      │
        │ 2018-10-20 00:00:00 │ IM1811025 │ 2018-11-05 00:00:00 │ 24720475M │ CT-YCN-BASE-WHITE            │ 55000        │ 10043            │ ABS-532X02-T.NL    │ 156.0                │ 10091                │
        │ 2019-01-25 00:00:00 │ IM1902119 │ 2019-02-20 00:00:00 │ 24720326M │ CT-CAX-CARTRIDGE-BASE        │ 340000       │ 9915540700       │ PS-RE-GPCD40T-T.NL │ 767.0                │                      │
        │ 2019-01-25 00:00:00 │ IM1902120 │ 2019-02-20 00:00:00 │ 24720327M │ CT-CAX-BASE-COVER            │ 175000       │ 9915540700       │ PS-RE-GPCD40T-T.NL │ 568.0                │                      │
        │ 2019-01-25 00:00:00 │ IM1902121 │ 2019-02-20 00:00:00 │ 24720328M │ CT-CAX-REEL                  │ 410000       │ 9915740199       │ POM-RE-F20-T.NL    │ 1200.0               │                      │
        │ 2019-01-25 00:00:00 │ IM1902129 │ 2019-02-20 00:00:00 │ 260501M   │ CT-PXN-HEAD-COVER-4.2MM      │ 55000        │ 10044            │ ABS-PA-757-T.NL    │ 56.0                 │ 10098                │
        │ 2019-01-25 00:00:00 │ IM1902134 │ 2019-02-20 00:00:00 │ 281709M   │ CT-PS-SPACER                 │ 30000        │ 9915540700       │ PS-RE-GPCD40T-T.NL │ 38.0                 │                      │
        └─────────────────────┴───────────┴─────────────────────┴───────────┴──────────────────────────────┴──────────────┴──────────────────┴────────────────────┴──────────────────────┴──────────────────────┘
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: itemCompositionSummary
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 121
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 121 rows × 11 columns
           (showing first/last 5 rows, showing first 10 columns)
        
        ┌──────────┬────────────────────────┬──────────────────┬────────────────────┬──────────────────────┬──────────────────────┬────────────────────────────┬──────────────────────────┬─────────────────────────┬─────────────────────┐
        │ itemCode │        itemName        │ plasticResinCode │    plasticResin    │ plasticResinQuantity │ colorMasterbatchCode │      colorMasterbatch      │ colorMasterbatchQuantity │ additiveMasterbatchCode │ additiveMasterbatch │
        ├──────────┼────────────────────────┼──────────────────┼────────────────────┼──────────────────────┼──────────────────────┼────────────────────────────┼──────────────────────────┼─────────────────────────┼─────────────────────┤
        │ 10236M   │ AB-TP-BODY             │ 10050            │ PP-VN-J106MG-T.NL  │ 50.36                │ 9917349000           │ MB-ABT-(3-28-33059)-L.GRAY │ 0.92                     │                         │                     │
        │ 10238M   │ AB-TP-LARGE-CAP-020-IY │ 10049            │ PP-VN-J2023GR-T.NL │ 29.02                │ 9917349020           │ MB-ABT-(3-12-9635)-020-IY  │ 0.18                     │                         │                     │
        │ 10239M   │ AB-TP-LARGE-CAP-025-YW │ 10049            │ PP-VN-J2023GR-T.NL │ 28.99                │ 9917349025           │ MB-ABT-(3-14-12381)-025-YW │ 0.2                      │                         │                     │
        │ 10240M   │ AB-TP-LARGE-CAP-026-YW │ 10049            │ PP-VN-J2023GR-T.NL │ 29.09                │ 9917349026           │ MB-ABT-(3-14-12382)-026-YW │ 0.1                      │                         │                     │
        │ 10241M   │ AB-TP-LARGE-CAP-027-BG │ 10049            │ PP-VN-J2023GR-T.NL │ 29.02                │ 9917349027           │ MB-ABT-(3-23-8309)-027-BG  │ 0.18                     │                         │                     │
        │ 291105M  │ CT-PGX-REEL-6.0MM-PINK │ 9913740599       │ POM-M9044-T.NL     │ 23.7                 │ 10096                │ MB-REF-49102-PINK          │ 0.99                     │                         │                     │
        │ 291305M  │ CT-PGX-CORE-6.0-PINK   │ 10044            │ ABS-PA-757-T.NL    │ 9.49                 │ 10090                │ MB-RAF-39098-PINK          │ 0.4                      │                         │                     │
        │ 300201M  │ CT-YX-GEAR-CASE        │ 101104FJ         │ PS-RE-GPCD40T-T.NL │ 39.91                │                      │                            │                          │                         │                     │
        │ 300201M  │ CT-YX-GEAR-CASE        │ 9915540700       │ PS-RE-GPCD40T-T.NL │ 49.88                │                      │                            │                          │                         │                     │
        │ 303001M  │ CT-YCN-CORE-BLUE       │ 10044            │ ABS-PA-757-T.NL    │ 5.13                 │ 10155                │ MB-MFABS-941-BLUE          │ 0.22                     │                         │                     │
        └──────────┴────────────────────────┴──────────────────┴────────────────────┴──────────────────────┴──────────────────────┴────────────────────────────┴──────────────────────────┴─────────────────────────┴─────────────────────┘
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: itemInfo
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 115
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 115 rows × 2 columns
           (showing first/last 5 rows)
        
        ┌───────────┬──────────────────────────────┐
        │  itemCode │           itemName           │
        ├───────────┼──────────────────────────────┤
        │ 10236M    │ AB-TP-BODY                   │
        │ 10238M    │ AB-TP-LARGE-CAP-020-IY       │
        │ 10239M    │ AB-TP-LARGE-CAP-025-YW       │
        │ 10240M    │ AB-TP-LARGE-CAP-026-YW       │
        │ 10241M    │ AB-TP-LARGE-CAP-027-BG       │
        │ 303001M   │ CT-YCN-CORE-BLUE             │
        │ 24720469M │ CT-YCN-LARGE-GEAR-WHITE      │
        │ 24720467M │ CT-YCN-PRINTER-HEAD-2.5MM-NL │
        │ 24720468M │ CT-YCN-SMALL-GEAR-NL         │
        │ 300201M   │ CT-YX-GEAR-CASE              │
        └───────────┴──────────────────────────────┘
        
        📋 Data Types:
           • itemCode: string
           • itemName: string
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: machineInfo
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 11
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 11 rows × 9 columns
           (showing first/last 5 rows)
        
        ┌───────────┬─────────────┬─────────────┬──────────────────┬────────────────┬─────────────┬─────────────────────┬───────────────┬─────────────────────┐
        │ machineNo │ machineCode │ machineName │ manufacturerName │ machineTonnage │ changedTime │   layoutStartDate   │ layoutEndDate │ previousMachineCode │
        ├───────────┼─────────────┼─────────────┼──────────────────┼────────────────┼─────────────┼─────────────────────┼───────────────┼─────────────────────┤
        │ NO.01     │ MD50S-000   │ MD50S       │ Niigata          │ 50             │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.02     │ MD50S-001   │ MD50S       │ Niigata          │ 50             │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.03     │ EC50ST-000  │ EC50ST      │ Toshiba          │ 50             │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.04     │ J100ADS-000 │ J100ADS     │ JSW              │ 100            │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.05     │ J100ADS-001 │ J100ADS     │ JSW              │ 100            │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.07     │ MD100S-001  │ MD100S      │ Niigata          │ 100            │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.08     │ MD130S-000  │ MD130S      │ Niigata          │ 130            │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.09     │ MD130S-001  │ MD130S      │ Niigata          │ 130            │ 1           │ 2018-11-01 00:00:00 │               │                     │
        │ NO.10     │ CNS50-000   │ CNS50       │ Niigata          │ 50             │ 1           │ 2019-01-15 00:00:00 │               │                     │
        │ NO.11     │ CNS50-001   │ CNS50       │ Niigata          │ 50             │ 1           │ 2019-01-15 00:00:00 │               │                     │
        └───────────┴─────────────┴─────────────┴──────────────────┴────────────────┴─────────────┴─────────────────────┴───────────────┴─────────────────────┘
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: moldInfo
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 66
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 66 rows × 8 columns
           (showing first/last 5 rows)
        
        ┌────────────────┬────────────────────────────────┬────────────────────┬──────────────────┬────────────────┬─────────────────────┬─────────────┬──────────────┐
        │     moldNo     │            moldName            │ moldCavityStandard │ moldSettingCycle │ machineTonnage │   acquisitionDate   │ itemsWeight │ runnerWeight │
        ├────────────────┼────────────────────────────────┼────────────────────┼──────────────────┼────────────────┼─────────────────────┼─────────────┼──────────────┤
        │ 20400IBE-M-001 │ AB-TP-BODY-M-0001              │ 4                  │ 36               │ 50/100/130/180 │ 2018-09-07 00:00:00 │ 3.7         │ 5.35         │
        │ 20101IBE-M-001 │ AB-TP-LARGE-CAP-M-0001         │ 4                  │ 21               │ 50/100         │ 2018-09-13 00:00:00 │ 1.8         │ 4.27         │
        │ 20101IBE-M-002 │ AB-TP-LARGE-CAP-M-0002         │ 4                  │ 21               │ 50/100         │ 2018-10-31 00:00:00 │ 1.8         │ 4.27         │
        │ 20102IBE-M-001 │ AB-TP-SMALL-CAP-M-0001         │ 4                  │ 18               │ 50/100         │ 2018-09-13 00:00:00 │ 0.74        │ 4.0          │
        │ 20102IBE-M-002 │ AB-TP-SMALL-CAP-M-0002         │ 4                  │ 18               │ 50/100         │ 2018-10-31 00:00:00 │ 0.74        │ 4.0          │
        │ 16200CBG-M-001 │ CT-YCN-CORE-M-0001             │ 16                 │ 15               │ 50/100         │ 2013-08-08 00:00:00 │ 0.05        │ 1.9          │
        │ 11000CBG-M-001 │ CT-YCN-LARGE-GEAR-M-0001       │ 4                  │ 18               │ 50             │ 2013-09-04 00:00:00 │ 0.2         │ 2.1          │
        │ 12000CBG-M-001 │ CT-YCN-PRINTER-HEAD-2.5-M-0001 │ 8                  │ 18               │ 50/100/180     │ 2013-07-12 00:00:00 │ 0.3         │ 3.5          │
        │ 11100CBG-M-001 │ CT-YCN-SMALL-GEAR-M-0001       │ 4                  │ 21               │ 50/100/180     │ 2013-09-10 00:00:00 │ 0.63        │ 3.1          │
        │ YXGC-M-003     │ CT-YX-GEAR-CASE-M-0003         │ 4                  │ 24               │ 50/100/130/180 │ 2008-12-01 00:00:00 │ 3.35        │ 6.2          │
        └────────────────┴────────────────────────────────┴────────────────────┴──────────────────┴────────────────┴─────────────────────┴─────────────┴──────────────┘
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: moldSpecificationSummary
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 116
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 116 rows × 5 columns
           (showing first/last 5 rows)
        
        ┌──────────┬────────────────────────┬─────────────────┬─────────┬────────────────┐
        │ itemCode │        itemName        │     itemType    │ moldNum │    moldList    │
        ├──────────┼────────────────────────┼─────────────────┼─────────┼────────────────┤
        │ 10236M   │ AB-TP-BODY             │ AB-TP-BODY      │ 1       │ 20400IBE-M-001 │
        │ 10238M   │ AB-TP-LARGE-CAP-020-IY │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │
        │ 10239M   │ AB-TP-LARGE-CAP-025-YW │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │
        │ 10240M   │ AB-TP-LARGE-CAP-026-YW │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │
        │ 10241M   │ AB-TP-LARGE-CAP-027-BG │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │
        │ 291103M  │ CT-PGX-REEL-5.0MM-BLUE │ CT-PGX-REEL     │ 1       │ 15001CAF-M-002 │
        │ 291105M  │ CT-PGX-REEL-6.0MM-PINK │ CT-PGX-REEL     │ 1       │ 15001CAF-M-002 │
        │ 291305M  │ CT-PGX-CORE-6.0-PINK   │ CT-PGX-CR6.0    │ 1       │ PGXCR6-M-001   │
        │ 300201M  │ CT-YX-GEAR-CASE        │ CT-Y-GEAR-CASE  │ 1       │ YXGC-M-003     │
        │ 303001M  │ CT-YCN-CORE-BLUE       │ CT-YCN-CORE     │ 1       │ 16200CBG-M-001 │
        └──────────┴────────────────────────┴─────────────────┴─────────┴────────────────┘
        
        📋 Data Types:
           • itemCode: string
           • itemName: string
           • itemType: string
           • moldNum: Int64
           • moldList: string
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • DATABASE_NAME: resinInfo
      • DATABASE_TYPE: staticDB
      • STATUS: success
      • RECORDS_PROCESSED: 78
      • DATA_UPDATED: True
      • DATAFRAME:
        📊 Shape: 78 rows × 4 columns
           (showing first/last 5 rows)
        
        ┌────────────┬────────────────────────────┬──────────────────┬────────────┐
        │ resinCode  │         resinName          │    resinType     │ colorType  │
        ├────────────┼────────────────────────────┼──────────────────┼────────────┤
        │ 10043      │ ABS-532X02-T.NL            │ plasticResin     │ natural    │
        │ 10044      │ ABS-PA-757-T.NL            │ plasticResin     │ natural    │
        │ 10045      │ ABS-PA-758-T.NL            │ plasticResin     │ natural    │
        │ 10046      │ PP-VN-J2021GR-T.NL         │ plasticResin     │ natural    │
        │ 10048      │ PC122-T.NL                 │ plasticResin     │ natural    │
        │ 9917349879 │ MB-ABT-(3-24-20107)-879-BN │ colorMasterbatch │ brown      │
        │ 9917349910 │ MB-ABT-(3-23-8814)-910-PK  │ colorMasterbatch │ pink       │
        │ 9917349942 │ MB-ABT-(3-23-8312)-942-BG  │ colorMasterbatch │ blue-green │
        │ 101104FJ   │ PS-RE-GPCD40T-T.NL         │ plasticResin     │ natural    │
        │ 9917349N15 │ MB-ABT-(3-29-4246)-N15-BK  │ colorMasterbatch │ black      │
        └────────────┴────────────────────────────┴──────────────────┴────────────┘
        
        📋 Data Types:
           • resinCode: string
           • resinName: string
           • resinType: string
           • colorType: string
      • EXISTING_PATH: 
      • WARNINGS: Existing file not found: 
      • RECOVERY_ACTIONS: 
      • OPERATION: file_save
      • STATUS: success
      • FILES_SAVED: 8
      • SAVED_FILES: productRecords, purchaseOrders, itemCompositionSummary, itemInfo, machineInfo, moldInfo, moldSpecificationSummary, resinInfo
      • OUTPUT_DIRECTORY: tests/shared_db/DataLoaderAgent
  • HEALING_ACTIONS: 
  • TRIGGER_AGENTS: ValidationOrchestrator
  • METADATA:
    • PROCESSING_DURATION_SECONDS: 1.344917
    • MEMORY_USAGE:
      • MEMORY_MB: 303.26171875
      • MEMORY_PERCENT: 2.3367453698519967
    • DISK_USAGE:
      • OUTPUT_DIRECTORY_MB: 0.11879253387451172
      • AVAILABLE_SPACE_MB: 70352.44921875
• TIMESTAMP: 2025-08-23 19:13:41
================================================================================
RESULTS OF CHANGE DETECTION IN PURCHASE ORDERS
================================================================================

Changes detected in databases => Proceeding to update shared databases...
Details: 
  - productRecords
  - purchaseOrders
  - productRecords
  - purchaseOrders
  - itemCompositionSummary
  - itemInfo
  - machineInfo
  - moldInfo
  - moldSpecificationSummary
  - resinInfo
===================================
GENERATED SHARED DATABASE BUILDING REPORTS
===================================

================================================================================
VALIDATION ORCHESTRATOR REPORT
================================================================================

• STATIC_MISMATCH:
  • PURCHASEORDERS:
    📊 Shape: 2 rows × 5 columns
    
    ┌───────────┬──────────────────────┬────────────────────────────────┬──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │    poNo   │     warningType      │          mismatchType          │                        requiredAction                        │                                                                                                     message                                                                                                      │
    ├───────────┼──────────────────────┼────────────────────────────────┼──────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ IM1902002 │ item_info_warnings   │ item_code_and_name_not_matched │ update_itemInfo_or_double_check_purchaseOrders               │ (IM1902002, 10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_not_matched. Please update_itemInfo_or_double_check_purchaseOrders                                                     │
    │ IM1902002 │ composition_warnings │ item_composition_not_matched   │ update_itemCompositionSummary_or_double_check_purchaseOrders │ (IM1902002) - Mismatch: 10242M, AB-TP-LARGE-CAP-055-YW, 10049, PP-VN-J2023GR-T.NL, 9917349055, MB-ABT-(3-14-12378)-055-YW, , _not_matched - Please: update_itemCompositionSummary_or_double_check_purchaseOrders │
    └───────────┴──────────────────────┴────────────────────────────────┴──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • poNo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
  • PRODUCTRECORDS:
    📊 Shape: 3 rows × 5 columns
    
    ┌───────────┬──────────────────────┬─────────────────────────────────┬──────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │    poNo   │     warningType      │           mismatchType          │                        requiredAction                        │                                                                                                          message                                                                                                          │
    ├───────────┼──────────────────────┼─────────────────────────────────┼──────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ IM1901044 │ item_info_warnings   │ item_code_and_name_not_matched  │ update_itemInfo_or_double_check_productRecords               │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: 260501M1_and_CT-PXN-HEAD-COVER-4.2MM_not_matched. Please update_itemInfo_or_double_check_productRecords                                  │
    │ IM1901044 │ resin_info_warnings  │ resin_code_and_name_not_matched │ update_resinInfo_or_double_check_productRecords              │ (IM1901044, 2019-01-31, 3, NO.11, 10043, ABS-PA-757-T.NL) - Mismatch: 10043_and_ABS-PA-757-T.NL_not_matched. Please update_resinInfo_or_double_check_productRecords                                                       │
    │ IM1901044 │ composition_warnings │ item_composition_not_matched    │ update_itemCompositionSummary_or_double_check_productRecords │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043, ABS-PA-757-T.NL, 10098, MB-GAF-49121-GREEN, , _not_matched - Please: update_itemCompositionSummary_or_double_check_productRecords │
    └───────────┴──────────────────────┴─────────────────────────────────┴──────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • poNo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
• PO_REQUIRED_MISMATCH:
  📊 Shape: 1 rows × 5 columns
  
  ┌───────────┬──────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │    poNo   │       warningType        │                                           mismatchType                                          │                  requiredAction                 │                                                                                message                                                                                │
  ├───────────┼──────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ IM1901044 │ product_info_not_matched │ PO was produced incorrectly with purchaseOrders. Details: plasticResinCode_itemCode_not_matched │ stop progressing or double check productRecords │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: plasticResinCode: 10043 vs 10044, itemCode: 260501M1 vs 260501M. Please stop progressing or double check productRecords │
  └───────────┴──────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  
  📋 Data Types:
     • poNo: object
     • warningType: object
     • mismatchType: object
     • requiredAction: object
     • message: object
• DYNAMIC_MISMATCH:
  • INVALID_ITEMS:
    📊 Shape: 1 rows × 5 columns
    
    ┌────────────────────────────────┬────────────────────────────────────────┬───────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │            itemInfo            │              warningType               │                  mismatchType                 │                          requiredAction                         │                                                                                             message                                                                                             │
    ├────────────────────────────────┼────────────────────────────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ 10242M, AB-TP-LARGE-CAP-055-YW │ item_invalid_in_itemCompositionSummary │ item_does_not_exist_in_itemCompositionSummary │ update_itemCompositionSummary_or_double_check_related_databases │ (10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_does_not_exist_in_itemCompositionSummary. Please update_itemCompositionSummary_or_double_check_related_databases │
    └────────────────────────────────┴────────────────────────────────────────┴───────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • itemInfo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
  • INFO_MISMATCHES:
    📊 Shape: 4 rows × 5 columns
    
    ┌───────────┬───────────────────────────────┬───────────────────────────────────────┬────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │    poNo   │          warningType          │              mismatchType             │                         requiredAction                         │                                                                                                                                                   message                                                                                                                                                   │
    ├───────────┼───────────────────────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ IM1901044 │ item_warnings                 │ item_info_not_matched                 │ update_itemInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: (260501M1, CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_itemInfo_or_double_check_productRecords                                                                                                                     │
    │ IM1901044 │ item_mold_warnings            │ item_and_mold_not_matched             │ update_moldInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002) - Mismatch: PXNHC4-M-002_and_(260501M1,CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_moldInfo_or_double_check_productRecords                                                                                       │
    │ IM1901044 │ mold_machine_tonnage_warnings │ mold_and_machine_tonnage_not_matched  │ update_moldSpecificationSummary_or_double_check_productRecords │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002, 50) - Mismatch: 50_and_PXNHC4-M-002_not_matched. Please update_moldSpecificationSummary_or_double_check_productRecords                                                                                                   │
    │ IM1901044 │ item_composition_warnings     │ item_and_item_composition_not_matched │ update_itemCompositionSummary_or_double_check_productRecords   │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN) - Mismatch: (260501M1,CT-PXN-HEAD-COVER-4.2MM)_and_10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN_not_matched. Please update_itemCompositionSummary_or_double_check_productRecords │
    └───────────┴───────────────────────────────┴───────────────────────────────────────┴────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • poNo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
• COMBINED_ALL:
  • ITEM_INVALID_WARNINGS:
    📊 Shape: 1 rows × 5 columns
    
    ┌────────────────────────────────┬────────────────────────────────────────┬───────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │            itemInfo            │              warningType               │                  mismatchType                 │                          requiredAction                         │                                                                                             message                                                                                             │
    ├────────────────────────────────┼────────────────────────────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ 10242M, AB-TP-LARGE-CAP-055-YW │ item_invalid_in_itemCompositionSummary │ item_does_not_exist_in_itemCompositionSummary │ update_itemCompositionSummary_or_double_check_related_databases │ (10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_does_not_exist_in_itemCompositionSummary. Please update_itemCompositionSummary_or_double_check_related_databases │
    └────────────────────────────────┴────────────────────────────────────────┴───────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • itemInfo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
  • PO_MISMATCH_WARNINGS:
    📊 Shape: 10 rows × 5 columns
    
    ┌───────────┬───────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │    poNo   │          warningType          │                                           mismatchType                                          │                         requiredAction                         │                                                                                                                                                   message                                                                                                                                                   │
    ├───────────┼───────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ IM1901044 │ item_warnings                 │ item_info_not_matched                                                                           │ update_itemInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: (260501M1, CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_itemInfo_or_double_check_productRecords                                                                                                                     │
    │ IM1901044 │ item_mold_warnings            │ item_and_mold_not_matched                                                                       │ update_moldInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002) - Mismatch: PXNHC4-M-002_and_(260501M1,CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_moldInfo_or_double_check_productRecords                                                                                       │
    │ IM1901044 │ mold_machine_tonnage_warnings │ mold_and_machine_tonnage_not_matched                                                            │ update_moldSpecificationSummary_or_double_check_productRecords │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002, 50) - Mismatch: 50_and_PXNHC4-M-002_not_matched. Please update_moldSpecificationSummary_or_double_check_productRecords                                                                                                   │
    │ IM1901044 │ item_composition_warnings     │ item_and_item_composition_not_matched                                                           │ update_itemCompositionSummary_or_double_check_productRecords   │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN) - Mismatch: (260501M1,CT-PXN-HEAD-COVER-4.2MM)_and_10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN_not_matched. Please update_itemCompositionSummary_or_double_check_productRecords │
    │ IM1902002 │ item_info_warnings            │ item_code_and_name_not_matched                                                                  │ update_itemInfo_or_double_check_purchaseOrders                 │ (IM1902002, 10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_not_matched. Please update_itemInfo_or_double_check_purchaseOrders                                                                                                                                                │
    │ IM1902002 │ composition_warnings          │ item_composition_not_matched                                                                    │ update_itemCompositionSummary_or_double_check_purchaseOrders   │ (IM1902002) - Mismatch: 10242M, AB-TP-LARGE-CAP-055-YW, 10049, PP-VN-J2023GR-T.NL, 9917349055, MB-ABT-(3-14-12378)-055-YW, , _not_matched - Please: update_itemCompositionSummary_or_double_check_purchaseOrders                                                                                            │
    │ IM1901044 │ item_info_warnings            │ item_code_and_name_not_matched                                                                  │ update_itemInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: 260501M1_and_CT-PXN-HEAD-COVER-4.2MM_not_matched. Please update_itemInfo_or_double_check_productRecords                                                                                                                    │
    │ IM1901044 │ resin_info_warnings           │ resin_code_and_name_not_matched                                                                 │ update_resinInfo_or_double_check_productRecords                │ (IM1901044, 2019-01-31, 3, NO.11, 10043, ABS-PA-757-T.NL) - Mismatch: 10043_and_ABS-PA-757-T.NL_not_matched. Please update_resinInfo_or_double_check_productRecords                                                                                                                                         │
    │ IM1901044 │ composition_warnings          │ item_composition_not_matched                                                                    │ update_itemCompositionSummary_or_double_check_productRecords   │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043, ABS-PA-757-T.NL, 10098, MB-GAF-49121-GREEN, , _not_matched - Please: update_itemCompositionSummary_or_double_check_productRecords                                                                                   │
    │ IM1901044 │ product_info_not_matched      │ PO was produced incorrectly with purchaseOrders. Details: plasticResinCode_itemCode_not_matched │ stop progressing or double check productRecords                │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: plasticResinCode: 10043 vs 10044, itemCode: 260501M1 vs 260501M. Please stop progressing or double check productRecords                                                                                                                                       │
    └───────────┴───────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
    
    📋 Data Types:
       • poNo: object
       • warningType: object
       • mismatchType: object
       • requiredAction: object
       • message: object
================================================================================
ORDER PROGRESS TRACKER REPORT
================================================================================

• PRODUCTIONSTATUS:
  📊 Shape: 190 rows × 31 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬──────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┬────────────────────┬───────────┐
  │ poReceivedDate │    poNo   │  itemCode │           itemName           │   poETA    │ itemQuantity │ itemRemain │ startedDate │ actualFinishedDate │ proStatus │
  ├────────────────┼───────────┼───────────┼──────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┼────────────────────┼───────────┤
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ MOLDED    │
  │ 2018-10-20     │ IM1811008 │ 24720318M │ CT-CAX-UPPER-CASE-BLUE       │ 2018-11-05 │ 30000        │ 0          │ 2018-11-01  │ 2018-11-02         │ MOLDED    │
  │ 2018-10-20     │ IM1811015 │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY      │ 2018-11-05 │ 15000        │ 0          │ 2018-11-01  │ 2018-11-02         │ MOLDED    │
  │ 2018-10-20     │ IM1811016 │ 24720326M │ CT-CAX-CARTRIDGE-BASE        │ 2018-11-05 │ 270000       │ 0          │ 2018-11-01  │ 2018-11-22         │ MOLDED    │
  │ 2018-10-20     │ IM1811025 │ 24720475M │ CT-YCN-BASE-WHITE            │ 2018-11-05 │ 55000        │ 0          │ 2018-11-01  │ 2018-11-21         │ MOLDED    │
  │ 2019-01-25     │ IM1902119 │ 24720326M │ CT-CAX-CARTRIDGE-BASE        │ 2019-02-20 │ 340000       │ 340000     │             │                    │ PENDING   │
  │ 2019-01-25     │ IM1902120 │ 24720327M │ CT-CAX-BASE-COVER            │ 2019-02-20 │ 175000       │ 175000     │             │                    │ PENDING   │
  │ 2019-01-25     │ IM1902121 │ 24720328M │ CT-CAX-REEL                  │ 2019-02-20 │ 410000       │ 410000     │             │                    │ PENDING   │
  │ 2019-01-25     │ IM1902129 │ 260501M   │ CT-PXN-HEAD-COVER-4.2MM      │ 2019-02-20 │ 55000        │ 55000      │             │                    │ PENDING   │
  │ 2019-01-25     │ IM1902134 │ 281709M   │ CT-PS-SPACER                 │ 2019-02-20 │ 30000        │ 30000      │             │                    │ PENDING   │
  └────────────────┴───────────┴───────────┴──────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┴────────────────────┴───────────┘
• MATERIALCOMPONENTMAP:
  📊 Shape: 180 rows × 13 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬─────────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┬────────────────────┬──────────────────┐
  │ poReceivedDate │    poNo   │  itemCode │             itemName            │   poETA    │ itemQuantity │ itemRemain │ startedDate │ actualFinishedDate │ plasticResinCode │
  ├────────────────┼───────────┼───────────┼─────────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┼────────────────────┼──────────────────┤
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT)    │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 10045            │
  │ 2018-10-20     │ IM1811008 │ 24720318M │ CT-CAX-UPPER-CASE-BLUE          │ 2018-11-05 │ 30000        │ 0          │ 2018-11-01  │ 2018-11-02         │ 10048            │
  │ 2018-10-20     │ IM1811015 │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY         │ 2018-11-05 │ 15000        │ 0          │ 2018-11-01  │ 2018-11-02         │ 9915740199       │
  │ 2018-10-20     │ IM1811016 │ 24720326M │ CT-CAX-CARTRIDGE-BASE           │ 2018-11-05 │ 270000       │ 0          │ 2018-11-01  │ 2018-11-22         │ 9915540700       │
  │ 2018-10-20     │ IM1811025 │ 24720475M │ CT-YCN-BASE-WHITE               │ 2018-11-05 │ 55000        │ 0          │ 2018-11-01  │ 2018-11-21         │ 10043            │
  │ 2019-01-02     │ IM1901060 │ 281709M   │ CT-PS-SPACER                    │ 2019-01-30 │ 30000        │ 0          │ 2019-01-31  │ 2019-01-31         │ 9915540700       │
  │ 2019-01-02     │ IM1901061 │ 290701M   │ CT-PGX-KNOCK-COVER              │ 2019-01-30 │ 40000        │ 0          │ 2019-01-22  │ 2019-01-23         │ 10045            │
  │ 2019-01-02     │ IM1901062 │ 290801M   │ CT-PGX-PRINTER-HEAD-4.2MM-GREEN │ 2019-01-30 │ 85000        │ 0          │ 2019-01-03  │ 2019-01-07         │ 10046            │
  │ 2019-01-02     │ IM1901063 │ 291103M   │ CT-PGX-REEL-5.0MM-BLUE          │ 2019-01-30 │ 21000        │ 0          │ 2019-01-15  │ 2019-01-16         │ 9913740599       │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE                │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 10044            │
  └────────────────┴───────────┴───────────┴─────────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┴────────────────────┴──────────────────┘
• MOLDSHOTMAP:
  📊 Shape: 181 rows × 12 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬─────────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┬────────────────────┬────────────────┐
  │ poReceivedDate │    poNo   │  itemCode │             itemName            │   poETA    │ itemQuantity │ itemRemain │ startedDate │ actualFinishedDate │     moldNo     │
  ├────────────────┼───────────┼───────────┼─────────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┼────────────────────┼────────────────┤
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT)    │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 14000CBQ-M-001 │
  │ 2018-10-20     │ IM1811008 │ 24720318M │ CT-CAX-UPPER-CASE-BLUE          │ 2018-11-05 │ 30000        │ 0          │ 2018-11-01  │ 2018-11-02         │ 10100CBR-M-001 │
  │ 2018-10-20     │ IM1811015 │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY         │ 2018-11-05 │ 15000        │ 0          │ 2018-11-01  │ 2018-11-02         │ 16500CBR-M-001 │
  │ 2018-10-20     │ IM1811016 │ 24720326M │ CT-CAX-CARTRIDGE-BASE           │ 2018-11-05 │ 270000       │ 0          │ 2018-11-01  │ 2018-11-22         │ 14000CBR-M-001 │
  │ 2018-10-20     │ IM1811025 │ 24720475M │ CT-YCN-BASE-WHITE               │ 2018-11-05 │ 55000        │ 0          │ 2018-11-01  │ 2018-11-21         │ 14000CBG-M-001 │
  │ 2019-01-02     │ IM1901060 │ 281709M   │ CT-PS-SPACER                    │ 2019-01-30 │ 30000        │ 0          │ 2019-01-31  │ 2019-01-31         │ PSSP-M-001     │
  │ 2019-01-02     │ IM1901061 │ 290701M   │ CT-PGX-KNOCK-COVER              │ 2019-01-30 │ 40000        │ 0          │ 2019-01-22  │ 2019-01-23         │ 17101CAF-M-002 │
  │ 2019-01-02     │ IM1901062 │ 290801M   │ CT-PGX-PRINTER-HEAD-4.2MM-GREEN │ 2019-01-30 │ 85000        │ 0          │ 2019-01-03  │ 2019-01-07         │ PGXPH42-M-001  │
  │ 2019-01-02     │ IM1901063 │ 291103M   │ CT-PGX-REEL-5.0MM-BLUE          │ 2019-01-30 │ 21000        │ 0          │ 2019-01-15  │ 2019-01-16         │ 15001CAF-M-002 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE                │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 16200CBG-M-001 │
  └────────────────┴───────────┴───────────┴─────────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┴────────────────────┴────────────────┘
• MACHINEQUANTITYMAP:
  📊 Shape: 196 rows × 12 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬─────────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┬────────────────────┬───────────────────┐
  │ poReceivedDate │    poNo   │  itemCode │             itemName            │   poETA    │ itemQuantity │ itemRemain │ startedDate │ actualFinishedDate │    machineCode    │
  ├────────────────┼───────────┼───────────┼─────────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┼────────────────────┼───────────────────┤
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT)    │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ NO.01_MD50S-000   │
  │ 2018-10-20     │ IM1811008 │ 24720318M │ CT-CAX-UPPER-CASE-BLUE          │ 2018-11-05 │ 30000        │ 0          │ 2018-11-01  │ 2018-11-02         │ NO.08_MD130S-000  │
  │ 2018-10-20     │ IM1811015 │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY         │ 2018-11-05 │ 15000        │ 0          │ 2018-11-01  │ 2018-11-02         │ NO.02_MD50S-001   │
  │ 2018-10-20     │ IM1811016 │ 24720326M │ CT-CAX-CARTRIDGE-BASE           │ 2018-11-05 │ 270000       │ 0          │ 2018-11-01  │ 2018-11-22         │ NO.07_MD100S-001  │
  │ 2018-10-20     │ IM1811016 │ 24720326M │ CT-CAX-CARTRIDGE-BASE           │ 2018-11-05 │ 270000       │ 0          │ 2018-11-01  │ 2018-11-22         │ NO.09_MD130S-001  │
  │ 2019-01-02     │ IM1901060 │ 281709M   │ CT-PS-SPACER                    │ 2019-01-30 │ 30000        │ 0          │ 2019-01-31  │ 2019-01-31         │ NO.10_CNS50-000   │
  │ 2019-01-02     │ IM1901061 │ 290701M   │ CT-PGX-KNOCK-COVER              │ 2019-01-30 │ 40000        │ 0          │ 2019-01-22  │ 2019-01-23         │ NO.11_CNS50-001   │
  │ 2019-01-02     │ IM1901062 │ 290801M   │ CT-PGX-PRINTER-HEAD-4.2MM-GREEN │ 2019-01-30 │ 85000        │ 0          │ 2019-01-03  │ 2019-01-07         │ NO.04_J100ADS-000 │
  │ 2019-01-02     │ IM1901063 │ 291103M   │ CT-PGX-REEL-5.0MM-BLUE          │ 2019-01-30 │ 21000        │ 0          │ 2019-01-15  │ 2019-01-16         │ NO.05_J100ADS-001 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE                │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ NO.10_CNS50-000   │
  └────────────────┴───────────┴───────────┴─────────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┴────────────────────┴───────────────────┘
• DAYQUANTITYMAP:
  📊 Shape: 805 rows × 12 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬──────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┬────────────────────┬────────────┐
  │ poReceivedDate │    poNo   │  itemCode │           itemName           │   poETA    │ itemQuantity │ itemRemain │ startedDate │ actualFinishedDate │ workingDay │
  ├────────────────┼───────────┼───────────┼──────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┼────────────────────┼────────────┤
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 2018-11-01 │
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 2018-11-02 │
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 2018-11-03 │
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 2018-11-05 │
  │ 2018-10-20     │ IM1811001 │ 26001122M │ CT-CA-BASE-T.SMOKE(NO-PRINT) │ 2018-11-05 │ 280000       │ 0          │ 2018-11-01  │ 2018-12-19         │ 2018-11-06 │
  │ 2019-01-02     │ IM1901063 │ 291103M   │ CT-PGX-REEL-5.0MM-BLUE       │ 2019-01-30 │ 21000        │ 0          │ 2019-01-15  │ 2019-01-16         │ 2019-01-16 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE             │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 2019-01-25 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE             │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 2019-01-26 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE             │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 2019-01-28 │
  │ 2019-01-02     │ IM1901064 │ 303001M   │ CT-YCN-CORE-BLUE             │ 2019-01-30 │ 55000        │ 0          │ 2019-01-25  │ 2019-01-29         │ 2019-01-29 │
  └────────────────┴───────────┴───────────┴──────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┴────────────────────┴────────────┘
• NOTWORKINGSTATUS:
  📊 Shape: 104 rows × 34 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────┬──────────────┬───────────┬─────────────┬───────────┬─────────────────────────────────────┬──────────────┬─────────────┬────────────────┬───────────┐
  │ recordDate │ workingShift │ machineNo │ machineCode │  itemCode │               itemName              │ colorChanged │ moldChanged │ machineChanged │   poNote  │
  ├────────────┼──────────────┼───────────┼─────────────┼───────────┼─────────────────────────────────────┼──────────────┼─────────────┼────────────────┼───────────┤
  │ 2018-11-01 │ 1            │ NO.02     │ MD50S-001   │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY             │              │             │                │ IM1811015 │
  │ 2018-11-01 │ 1            │ NO.09     │ MD130S-001  │           │                                     │              │             │                │           │
  │ 2018-11-01 │ 2            │ NO.02     │ MD50S-001   │ 24720325M │ CT-CAX-LOCK-BUTTON-GRAY             │              │             │                │ IM1811015 │
  │ 2018-11-05 │ 2            │ NO.07     │ MD100S-001  │           │                                     │              │             │                │           │
  │ 2018-11-05 │ 3            │ NO.04     │ J100ADS-000 │ 26004630M │ CT-CA-PRINTER-HEAD-5.0MM-LIGHT-BLUE │              │             │                │ IM1811030 │
  │ 2019-01-30 │ 2            │ NO.04     │ J100ADS-000 │           │                                     │              │             │                │           │
  │ 2019-01-30 │ 3            │ NO.04     │ J100ADS-000 │           │                                     │              │             │                │           │
  │ 2019-01-31 │ 1            │ NO.04     │ J100ADS-000 │           │                                     │              │             │                │           │
  │ 2019-01-31 │ 2            │ NO.04     │ J100ADS-000 │           │                                     │              │             │                │           │
  │ 2019-01-31 │ 3            │ NO.04     │ J100ADS-000 │           │                                     │              │             │                │           │
  └────────────┴──────────────┴───────────┴─────────────┴───────────┴─────────────────────────────────────┴──────────────┴─────────────┴────────────────┴───────────┘
• ITEM_INVALID_WARNINGS:
  📊 Shape: 1 rows × 5 columns
  
  ┌────────────────────────────────┬────────────────────────────────────────┬───────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │            itemInfo            │              warningType               │                  mismatchType                 │                          requiredAction                         │                                                                                             message                                                                                             │
  ├────────────────────────────────┼────────────────────────────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 10242M, AB-TP-LARGE-CAP-055-YW │ item_invalid_in_itemCompositionSummary │ item_does_not_exist_in_itemCompositionSummary │ update_itemCompositionSummary_or_double_check_related_databases │ (10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_does_not_exist_in_itemCompositionSummary. Please update_itemCompositionSummary_or_double_check_related_databases │
  └────────────────────────────────┴────────────────────────────────────────┴───────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  
  📋 Data Types:
     • itemInfo: object
     • warningType: object
     • mismatchType: object
     • requiredAction: object
     • message: object
• PO_MISMATCH_WARNINGS:
  📊 Shape: 10 rows × 5 columns
  
  ┌───────────┬───────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │    poNo   │          warningType          │                                           mismatchType                                          │                         requiredAction                         │                                                                                                                                                   message                                                                                                                                                   │
  ├───────────┼───────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ IM1901044 │ item_warnings                 │ item_info_not_matched                                                                           │ update_itemInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: (260501M1, CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_itemInfo_or_double_check_productRecords                                                                                                                     │
  │ IM1901044 │ item_mold_warnings            │ item_and_mold_not_matched                                                                       │ update_moldInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002) - Mismatch: PXNHC4-M-002_and_(260501M1,CT-PXN-HEAD-COVER-4.2MM)_not_matched. Please update_moldInfo_or_double_check_productRecords                                                                                       │
  │ IM1901044 │ mold_machine_tonnage_warnings │ mold_and_machine_tonnage_not_matched                                                            │ update_moldSpecificationSummary_or_double_check_productRecords │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, PXNHC4-M-002, 50) - Mismatch: 50_and_PXNHC4-M-002_not_matched. Please update_moldSpecificationSummary_or_double_check_productRecords                                                                                                   │
  │ IM1901044 │ item_composition_warnings     │ item_and_item_composition_not_matched                                                           │ update_itemCompositionSummary_or_double_check_productRecords   │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN) - Mismatch: (260501M1,CT-PXN-HEAD-COVER-4.2MM)_and_10043_ABS-PA-757-T.NL | 10098_MB-GAF-49121-GREEN_not_matched. Please update_itemCompositionSummary_or_double_check_productRecords │
  │ IM1902002 │ item_info_warnings            │ item_code_and_name_not_matched                                                                  │ update_itemInfo_or_double_check_purchaseOrders                 │ (IM1902002, 10242M, AB-TP-LARGE-CAP-055-YW) - Mismatch: 10242M_and_AB-TP-LARGE-CAP-055-YW_not_matched. Please update_itemInfo_or_double_check_purchaseOrders                                                                                                                                                │
  │ IM1902002 │ composition_warnings          │ item_composition_not_matched                                                                    │ update_itemCompositionSummary_or_double_check_purchaseOrders   │ (IM1902002) - Mismatch: 10242M, AB-TP-LARGE-CAP-055-YW, 10049, PP-VN-J2023GR-T.NL, 9917349055, MB-ABT-(3-14-12378)-055-YW, , _not_matched - Please: update_itemCompositionSummary_or_double_check_purchaseOrders                                                                                            │
  │ IM1901044 │ item_info_warnings            │ item_code_and_name_not_matched                                                                  │ update_itemInfo_or_double_check_productRecords                 │ (IM1901044, 2019-01-31, 3, NO.11, 260501M1, CT-PXN-HEAD-COVER-4.2MM) - Mismatch: 260501M1_and_CT-PXN-HEAD-COVER-4.2MM_not_matched. Please update_itemInfo_or_double_check_productRecords                                                                                                                    │
  │ IM1901044 │ resin_info_warnings           │ resin_code_and_name_not_matched                                                                 │ update_resinInfo_or_double_check_productRecords                │ (IM1901044, 2019-01-31, 3, NO.11, 10043, ABS-PA-757-T.NL) - Mismatch: 10043_and_ABS-PA-757-T.NL_not_matched. Please update_resinInfo_or_double_check_productRecords                                                                                                                                         │
  │ IM1901044 │ composition_warnings          │ item_composition_not_matched                                                                    │ update_itemCompositionSummary_or_double_check_productRecords   │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: 260501M1, CT-PXN-HEAD-COVER-4.2MM, 10043, ABS-PA-757-T.NL, 10098, MB-GAF-49121-GREEN, , _not_matched - Please: update_itemCompositionSummary_or_double_check_productRecords                                                                                   │
  │ IM1901044 │ product_info_not_matched      │ PO was produced incorrectly with purchaseOrders. Details: plasticResinCode_itemCode_not_matched │ stop progressing or double check productRecords                │ (IM1901044, 2019-01-31, 3, NO.11) - Mismatch: plasticResinCode: 10043 vs 10044, itemCode: 260501M1 vs 260501M. Please stop progressing or double check productRecords                                                                                                                                       │
  └───────────┴───────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
  
  📋 Data Types:
     • poNo: object
     • warningType: object
     • mismatchType: object
     • requiredAction: object
     • message: object
================================================================================
RESULTS OF DETECTION IN SUFFICIENT DATE RECORDS
================================================================================

Date records are not sufficient for historical insights. => Skipping historical insight adding phase!!!
================================================================================
INITIAL PLANNER (PRODUCING PROGRESS) REPORT
================================================================================

• PRODUCING_STATUS_DATA:
  📊 Shape: 1 rows × 20 columns
     (showing first 10 columns)
  
  ┌───────────┬───────────┬─────────────────────────┬────────────┬────────────────┬──────────────┬────────────┬───────────┬─────────────────────┬───────────────────┐
  │    poNo   │  itemCode │         itemName        │   poETA    │     moldNo     │ itemQuantity │ itemRemain │ machineNo │     startedDate     │      moldName     │
  ├───────────┼───────────┼─────────────────────────┼────────────┼────────────────┼──────────────┼────────────┼───────────┼─────────────────────┼───────────────────┤
  │ IM1901040 │ 26003170M │ CT-CA-BASE-NL(NO-PRINT) │ 2019-01-30 │ 14000CBQ-M-001 │ 500000       │ 116267     │ NO.01     │ 2019-01-03 00:00:00 │ CT-CA-BASE-M-0001 │
  └───────────┴───────────┴─────────────────────────┴────────────┴────────────────┴──────────────┴────────────┴───────────┴─────────────────────┴───────────────────┘
• PRODUCING_PRO_PLAN:
  📊 Shape: 11 rows × 6 columns
     (showing first/last 5 rows)
  
  ┌───────────┬─────────────┬─────────────┬────────────────┬─────────────────────────────────────┬───────────────────────────┐
  │ machineNo │ machineCode │ machineName │ machineTonnage │            itemName_poNo            │         remainTime        │
  ├───────────┼─────────────┼─────────────┼────────────────┼─────────────────────────────────────┼───────────────────────────┤
  │ NO.01     │ MD50S-000   │ MD50S       │ 50             │ CT-CA-BASE-NL(NO-PRINT) (IM1901040) │ 3 days 16:37:05.304878047 │
  │ NO.02     │ MD50S-001   │ MD50S       │ 50             │                                     │                           │
  │ NO.03     │ EC50ST-000  │ EC50ST      │ 50             │                                     │                           │
  │ NO.04     │ J100ADS-000 │ J100ADS     │ 100            │                                     │                           │
  │ NO.05     │ J100ADS-001 │ J100ADS     │ 100            │                                     │                           │
  │ NO.07     │ MD100S-001  │ MD100S      │ 100            │                                     │                           │
  │ NO.08     │ MD130S-000  │ MD130S      │ 130            │                                     │                           │
  │ NO.09     │ MD130S-001  │ MD130S      │ 130            │                                     │                           │
  │ NO.10     │ CNS50-000   │ CNS50       │ 50             │                                     │                           │
  │ NO.11     │ CNS50-001   │ CNS50       │ 50             │                                     │                           │
  └───────────┴─────────────┴─────────────┴────────────────┴─────────────────────────────────────┴───────────────────────────┘
  
  📋 Data Types:
     • machineNo: object
     • machineCode: string
     • machineName: string
     • machineTonnage: Int64
     • itemName_poNo: object
     • remainTime: timedelta64[ns]
• PRODUCING_MOLD_PLAN:
  📊 Shape: 11 rows × 6 columns
     (showing first/last 5 rows)
  
  ┌───────────┬─────────────┬─────────────┬────────────────┬───────────────────┬───────────────────────────┐
  │ machineNo │ machineCode │ machineName │ machineTonnage │      moldName     │         remainTime        │
  ├───────────┼─────────────┼─────────────┼────────────────┼───────────────────┼───────────────────────────┤
  │ NO.01     │ MD50S-000   │ MD50S       │ 50             │ CT-CA-BASE-M-0001 │ 3 days 16:37:05.304878047 │
  │ NO.02     │ MD50S-001   │ MD50S       │ 50             │                   │                           │
  │ NO.03     │ EC50ST-000  │ EC50ST      │ 50             │                   │                           │
  │ NO.04     │ J100ADS-000 │ J100ADS     │ 100            │                   │                           │
  │ NO.05     │ J100ADS-001 │ J100ADS     │ 100            │                   │                           │
  │ NO.07     │ MD100S-001  │ MD100S      │ 100            │                   │                           │
  │ NO.08     │ MD130S-000  │ MD130S      │ 130            │                   │                           │
  │ NO.09     │ MD130S-001  │ MD130S      │ 130            │                   │                           │
  │ NO.10     │ CNS50-000   │ CNS50       │ 50             │                   │                           │
  │ NO.11     │ CNS50-001   │ CNS50       │ 50             │                   │                           │
  └───────────┴─────────────┴─────────────┴────────────────┴───────────────────┴───────────────────────────┘
  
  📋 Data Types:
     • machineNo: object
     • machineCode: string
     • machineName: string
     • machineTonnage: Int64
     • moldName: string
     • remainTime: timedelta64[ns]
• PRODUCING_PLASTIC_PLAN:
  📊 Shape: 11 rows × 12 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌───────────┬─────────────┬─────────────┬────────────────┬─────────────────────────────────────┬─────────────────────────┬─────────────────┬───────────────────────────────┬──────────────────┬───────────────────────────────────┐
  │ machineNo │ machineCode │ machineName │ machineTonnage │            itemName_poNo            │ estimatedOutputQuantity │   plasticResin  │ estimatedPlasticResinQuantity │ colorMasterbatch │ estimatedColorMasterbatchQuantity │
  ├───────────┼─────────────┼─────────────┼────────────────┼─────────────────────────────────────┼─────────────────────────┼─────────────────┼───────────────────────────────┼──────────────────┼───────────────────────────────────┤
  │ NO.01     │ MD50S-000   │ MD50S       │ 50             │ CT-CA-BASE-NL(NO-PRINT) (IM1901040) │ 38400                   │ ABS-PA-758-T.NL │ 87.4752                       │ NONE             │ 0.0                               │
  │ NO.02     │ MD50S-001   │ MD50S       │ 50             │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.03     │ EC50ST-000  │ EC50ST      │ 50             │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.04     │ J100ADS-000 │ J100ADS     │ 100            │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.05     │ J100ADS-001 │ J100ADS     │ 100            │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.07     │ MD100S-001  │ MD100S      │ 100            │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.08     │ MD130S-000  │ MD130S      │ 130            │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.09     │ MD130S-001  │ MD130S      │ 130            │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.10     │ CNS50-000   │ CNS50       │ 50             │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  │ NO.11     │ CNS50-001   │ CNS50       │ 50             │                                     │                         │ NONE            │ 0.0                           │ NONE             │ 0.0                               │
  └───────────┴─────────────┴─────────────┴────────────────┴─────────────────────────────────────┴─────────────────────────┴─────────────────┴───────────────────────────────┴──────────────────┴───────────────────────────────────┘
• PENDING_STATUS_DATA:
  📊 Shape: 12 rows × 5 columns
     (showing first/last 5 rows)
  
  ┌───────────┬───────────┬──────────────────────────┬────────────┬──────────────┐
  │    poNo   │  itemCode │         itemName         │   poETA    │ itemQuantity │
  ├───────────┼───────────┼──────────────────────────┼────────────┼──────────────┤
  │ IM1812004 │ 24720309M │ CT-YA-PRINTER-HEAD-4.2MM │ 2018-12-31 │ 2516         │
  │ IM1901020 │ 10236M    │ AB-TP-BODY               │ 2019-01-15 │ 10000        │
  │ IM1902001 │ 10241M    │ AB-TP-LARGE-CAP-027-BG   │ 2019-02-20 │ 2000         │
  │ IM1902002 │ 10242M    │ AB-TP-LARGE-CAP-055-YW   │ 2019-02-20 │ 15000        │
  │ IM1902047 │ 10350M    │ AB-TP-SMALL-CAP-062-YW   │ 2019-02-20 │ 22000        │
  │ IM1902119 │ 24720326M │ CT-CAX-CARTRIDGE-BASE    │ 2019-02-20 │ 340000       │
  │ IM1902120 │ 24720327M │ CT-CAX-BASE-COVER        │ 2019-02-20 │ 175000       │
  │ IM1902121 │ 24720328M │ CT-CAX-REEL              │ 2019-02-20 │ 410000       │
  │ IM1902129 │ 260501M   │ CT-PXN-HEAD-COVER-4.2MM  │ 2019-02-20 │ 55000        │
  │ IM1902134 │ 281709M   │ CT-PS-SPACER             │ 2019-02-20 │ 30000        │
  └───────────┴───────────┴──────────────────────────┴────────────┴──────────────┘
  
  📋 Data Types:
     • poNo: object
     • itemCode: object
     • itemName: object
     • poETA: object
     • itemQuantity: int64
• MOLD_MACHINE_PRIORITY_MATRIX:
  📊 Shape: 66 rows × 12 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌────────────────┬───────────┬───────────┬────────────┬─────────────┬─────────────┬────────────┬────────────┬────────────┬────────────┐
  │     moldNo     │ CNS50-000 │ CNS50-001 │ EC50ST-000 │ J100ADS-000 │ J100ADS-001 │ MD100S-000 │ MD100S-001 │ MD130S-000 │ MD130S-001 │
  ├────────────────┼───────────┼───────────┼────────────┼─────────────┼─────────────┼────────────┼────────────┼────────────┼────────────┤
  │ 10000CBR-M-001 │ 0         │ 0         │ 0          │ 0           │ 0           │ 0          │ 1          │ 2          │ 0          │
  │ 10000CBS-M-001 │ 0         │ 0         │ 0          │ 0           │ 0           │ 1          │ 0          │ 0          │ 0          │
  │ 10100CBR-M-001 │ 0         │ 0         │ 0          │ 0           │ 0           │ 2          │ 3          │ 1          │ 0          │
  │ 10100CBS-M-001 │ 0         │ 0         │ 0          │ 0           │ 0           │ 1          │ 0          │ 2          │ 0          │
  │ 11000CBG-M-001 │ 0         │ 0         │ 0          │ 0           │ 0           │ 0          │ 0          │ 0          │ 0          │
  │ PXNLS-M-001    │ 0         │ 0         │ 0          │ 0           │ 0           │ 0          │ 0          │ 0          │ 0          │
  │ PXNSC-M-001    │ 0         │ 0         │ 1          │ 0           │ 0           │ 0          │ 0          │ 0          │ 0          │
  │ PXNSG2-M-001   │ 0         │ 0         │ 0          │ 0           │ 1           │ 0          │ 0          │ 0          │ 0          │
  │ PXNSG5-M-001   │ 0         │ 0         │ 0          │ 0           │ 1           │ 0          │ 0          │ 2          │ 0          │
  │ YXGC-M-003     │ 0         │ 0         │ 0          │ 0           │ 0           │ 2          │ 0          │ 1          │ 3          │
  └────────────────┴───────────┴───────────┴────────────┴─────────────┴─────────────┴────────────┴────────────┴────────────┴────────────┘
• MOLD_ESTIMATED_CAPACITY_DF:
  📊 Shape: 124 rows × 13 columns
     (showing first/last 5 rows, showing first 10 columns)
  
  ┌──────────┬────────────────────────┬─────────────────┬─────────┬────────────────┬────────────────────────┬─────────────────────┬────────────────────┬──────────────────┬────────────────┐
  │ itemCode │        itemName        │     itemType    │ moldNum │     moldNo     │        moldName        │   acquisitionDate   │ moldCavityStandard │ moldSettingCycle │ machineTonnage │
  ├──────────┼────────────────────────┼─────────────────┼─────────┼────────────────┼────────────────────────┼─────────────────────┼────────────────────┼──────────────────┼────────────────┤
  │ 10236M   │ AB-TP-BODY             │ AB-TP-BODY      │ 1       │ 20400IBE-M-001 │ AB-TP-BODY-M-0001      │ 2018-09-07 00:00:00 │ 4                  │ 36               │ 50/100/130/180 │
  │ 10238M   │ AB-TP-LARGE-CAP-020-IY │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │ AB-TP-LARGE-CAP-M-0001 │ 2018-09-13 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 10239M   │ AB-TP-LARGE-CAP-025-YW │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │ AB-TP-LARGE-CAP-M-0001 │ 2018-09-13 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 10240M   │ AB-TP-LARGE-CAP-026-YW │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │ AB-TP-LARGE-CAP-M-0001 │ 2018-09-13 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 10241M   │ AB-TP-LARGE-CAP-027-BG │ AB-TP-LARGE-CAP │ 1       │ 20101IBE-M-001 │ AB-TP-LARGE-CAP-M-0001 │ 2018-09-13 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 291103M  │ CT-PGX-REEL-5.0MM-BLUE │ CT-PGX-REEL     │ 1       │ 15001CAF-M-002 │ CT-PGX-REEL-M-0002     │ 2013-10-18 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 291105M  │ CT-PGX-REEL-6.0MM-PINK │ CT-PGX-REEL     │ 1       │ 15001CAF-M-002 │ CT-PGX-REEL-M-0002     │ 2013-10-18 00:00:00 │ 4                  │ 21               │ 50/100         │
  │ 291305M  │ CT-PGX-CORE-6.0-PINK   │ CT-PGX-CR6.0    │ 1       │ PGXCR6-M-001   │ CT-PGX.PS-CR6.0-M-0001 │ 2008-05-01 00:00:00 │ 16                 │ 21               │ 50/100/130     │
  │ 300201M  │ CT-YX-GEAR-CASE        │ CT-Y-GEAR-CASE  │ 1       │ YXGC-M-003     │ CT-YX-GEAR-CASE-M-0003 │ 2008-12-01 00:00:00 │ 4                  │ 24               │ 50/100/130/180 │
  │ 303001M  │ CT-YCN-CORE-BLUE       │ CT-YCN-CORE     │ 1       │ 16200CBG-M-001 │ CT-YCN-CORE-M-0001     │ 2013-08-08 00:00:00 │ 16                 │ 15               │ 50/100         │
  └──────────┴────────────────────────┴─────────────────┴─────────┴────────────────┴────────────────────────┴─────────────────────┴────────────────────┴──────────────────┴────────────────┘
• INVALID_MOLDS:
  📊 Shape: 1 rows × 2 columns
  
  ┌──────────────────────────────────┬───────────────────────────────┐
  │ estimated_capacity_invalid_molds │ priority_matrix_invalid_molds │
  ├──────────────────────────────────┼───────────────────────────────┤
  │                                  │ PXNHC4-M-002                  │
  └──────────────────────────────────┴───────────────────────────────┘
  
  📋 Data Types:
     • estimated_capacity_invalid_molds: object
     • priority_matrix_invalid_molds: object
================================================================================
RESULTS OF CHANGE DETECTION IN PURCHASE ORDERS
================================================================================

Changes detected in purchaseOrders => Proceeding with initial planner...
===================================
INITIAL PLANNER (PENDING PROGRESS) REPORT
===================================

• INITIALPLAN:
  📊 Shape: 14 rows × 10 columns
     (showing first/last 5 rows)
  
  ┌─────────────┬──────────────┬────────────────┬───────────┬─────────────────────────┬─────────────┬─────────────────────┬────────────────┬─────────────────────┬───────────┐
  │ Machine No. │ Machine Code │ Assigned Mold  │   PO No.  │        Item Name        │ PO Quantity │    ETA (PO Date)    │ Mold Lead Time │ Priority in Machine │    Note   │
  ├─────────────┼──────────────┼────────────────┼───────────┼─────────────────────────┼─────────────┼─────────────────────┼────────────────┼─────────────────────┼───────────┤
  │ NO.01       │ MD50S-000    │                │           │                         │ 0           │                     │ 0              │ 0                   │ histBased │
  │ NO.02       │ MD50S-001    │ 20102IBE-M-001 │ IM1902047 │ AB-TP-SMALL-CAP-062-YW  │ 22000       │ 2019-02-20 00:00:00 │ 1              │ 1                   │ histBased │
  │ NO.03       │ EC50ST-000   │ PXNHC4-M-001   │ IM1902129 │ CT-PXN-HEAD-COVER-4.2MM │ 55000       │ 2019-02-20 00:00:00 │ 2              │ 1                   │ histBased │
  │ NO.04       │ J100ADS-000  │ 14000CBR-M-001 │ IM1902119 │ CT-CAX-CARTRIDGE-BASE   │ 340000      │ 2019-02-20 00:00:00 │ 14             │ 1                   │ histBased │
  │ NO.05       │ J100ADS-001  │ 15000CBR-M-001 │ IM1902121 │ CT-CAX-REEL             │ 410000      │ 2019-02-20 00:00:00 │ 17             │ 1                   │ histBased │
  │ NO.08       │ MD130S-000   │ 10100CBR-M-001 │ IM1902116 │ CT-CAX-UPPER-CASE-PINK  │ 180000      │ 2019-02-20 00:00:00 │ 15             │ 1                   │ histBased │
  │ NO.09       │ MD130S-001   │ 20400IBE-M-001 │ IM1901020 │ AB-TP-BODY              │ 10000       │ 2019-01-15 00:00:00 │ 1              │ 1                   │ histBased │
  │ NO.09       │ MD130S-001   │ 14100CBR-M-001 │ IM1902120 │ CT-CAX-BASE-COVER       │ 175000      │ 2019-02-20 00:00:00 │ 7              │ 2                   │ histBased │
  │ NO.10       │ CNS50-000    │ PSSP-M-001     │ IM1902134 │ CT-PS-SPACER            │ 30000       │ 2019-02-20 00:00:00 │ 1              │ 1                   │ histBased │
  │ NO.11       │ CNS50-001    │                │           │                         │ 0           │                     │ 0              │ 0                   │ histBased │
  └─────────────┴──────────────┴────────────────┴───────────┴─────────────────────────┴─────────────┴─────────────────────┴────────────────┴─────────────────────┴───────────┘
• INVALID_MOLDS:
  📊 Shape: 1 rows × 2 columns
  
  ┌───────────────────────────────┬──────────────┐
  │            category           │     mold     │
  ├───────────────────────────────┼──────────────┤
  │ priority_matrix_invalid_molds │ PXNHC4-M-002 │
  └───────────────────────────────┴──────────────┘
  
  📋 Data Types:
     • category: object
     • mold: object
================================================================================
PROGRESS_OUTPUT_COLLECTION
================================================================================

data_pipeline_orchestrator_path: tests/shared_db/DataPipelineOrchestrator/tests/shared_db/DataPipelineOrchestrator/newest/20250823_1913_DataCollector_success_report.txt
tests/shared_db/DataPipelineOrchestrator/tests/shared_db/DataPipelineOrchestrator/newest/20250823_1913_DataLoaderAgent_success_report.txt
tests/shared_db/DataPipelineOrchestrator/tests/shared_db/DataPipelineOrchestrator/newest/20250823_1913_DataPipelineOrchestrator_final_report.txt
order_progress_path: tests/shared_db/OrderProgressTracker/newest/20250823_1913_auto_status.xlsx
producing_plan_path: tests/shared_db/ProducingProcessor/newest/20250823_1913_producing_processor.xlsx
pending_initial_plan_path: tests/shared_db/PendingProcessor/newest/20250823_1913_pending_processor.xlsx



*** This report was automatically generated by the OptiMoldIQ Workflow system. ***

```