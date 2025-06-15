## 3. Dataset

### 3.1. Data Source and Collection
This research utilizes a comprehensive dataset from a plastic injection molding production facility. The dataset encompasses the production workflow, from order receipt to production planning and execution. Data was collected from the facility's enterprise resource planning (ERP) system and production management database over a 27-month period (1/11/2018 - 30/1/2021), resulting in a dataset with over 61,185 production records and 6,234 orders. This dataset captures the complexities and challenges of plastic part manufacturing operations and supports the development of intelligent production planning systems.

### 3.2. Dataset Structure
The dataset is structured around six primary entities that represent the core components of the injection molding production process:

- **Items**  
  Contains 694 unique plastic products with attributes including item code, item name, and item type. Each item represents a specific plastic component that can be manufactured.

- **Molds**  
  Comprises 251 distinct molds with detailed specifications such as mold code, mold name, mold status, number of cavities, and setting cycle time. Molds are the critical tooling used to shape plastic parts.

- **Machines**  
  Includes 49 injection molding machines with attributes such as machine code, machine name, manufacturer, machine tonnage, and operational parameters. The machine fleet expanded from an initial 9 machines to 49 machines during the data collection period, reflecting the company's significant growth and production capacity expansion. This scaling of equipment corresponds directly with the company's overall business expansion and increased manufacturing capabilities. Each machine has specific capabilities that determine which molds can be used with it.

- **Materials**  
  Records 445 different materials, including:
  - Base plastic resins (e.g., ABS, PP, PC)
  - Color masterbatches
  - Additives

- **Production Orders**  
  Contains 6,234 internal orders (one item type per order) with information on order dates, required quantities, and delivery deadlines. Orders are typically scheduled at the beginning and middle of each month, enabling the production department to autonomously develop manufacturing plans.

- **Production Records**  
  Encompasses 61,185 production runs documenting actual production outcomes, including good quantities, defect quantities by type, production dates, and cycle times.

### 3.3. Entity Relationships
The dataset captures several critical relationships that represent the production constraints and dependencies:

![EntityRelationshipDiagram](OptiMoldIQ-EntityRelationshipDiagram(ERD).png)

- **Item-Mold Relationship**  
  Each item can be produced using one or more specific molds. On average, each item is associated with 1.33 molds (min: 1, max: 3).

- **Mold-Machine Relationship**  
  Each mold can operate only on specific machines based on tonnage, clamping system, and technical requirements. On average, a mold is compatible with 1.83 machine tonnage types (min: 1, max: 4).

- **Item-Material Relationship**  
  Each item requires:
  - A specific plastic resin type
  - A designated color masterbatch
  - Optional additives based on product requirements

These relationships form a complex network of constraints that must be accounted for during production planning and scheduling.

### 3.4. Temporal Characteristics
The dataset exhibits several temporal patterns that reflect the operational behavior of the production facility:

- **Order Cyclicality**  
  Internal production orders are primarily scheduled at the beginning and middle of each month, introducing cyclical demand patterns into the production schedule.

- **Production Lead Times**  
  The time between order placement and production completion is captured in detail, with an average lead time of 9.25 days for standard orders.

- **Production Cycles**  
  Detailed cycle time data for each combination of item, mold, and machine are available, allowing analysis of production speed variations across configurations.

### 3.5. Quality Metrics
The dataset contains comprehensive quality information that enables fine-grained analysis of production outcomes:

- **Defect Types**  
  Records up to 10 defect categories, including:
  - BlackSpot, OilDeposit, Scratch, Crack, SinkMark, Short, Burst, Bend, Stain, and otherNG.

- **Defect Quantities**  
  The number of defective parts is recorded for each defect type in every production run.

- **Good Quantities**  
  Captures the total number of acceptable parts produced.

- **Quality Rates**  
  Computed as the ratio of good parts to total produced parts, enabling comparison of different item-mold-machine-material combinations.

### 3.6. Dataset Statistics
#### Table 1: Summary Statistics of the Dataset

| Entity              | Count   | Attributes                               | Example Fields                                                                 |
|---------------------|---------|------------------------------------------|--------------------------------------------------------------------------------|
| **Items**           | 694     | 3                                        | itemCode, itemName, itemType (from itemInfo, moldSpecification)               |
| **Molds**           | 251     | 7                                        | moldNo, moldName, moldCavityStandard, moldSettingCycle, moldStatus, moldNum, machineTonnage |
| **Machines**        | 49      | 6+                                       | machineNo, machineCode, machineName, machineTonnage, manufacturerName, layoutStartDate |
| **Materials**       | 445     | 6                                        | plasticResinCode, colorMasterbatchCode, additiveMasterbatchCode, plasticResin, colorMasterbatch, additiveMasterbatch |
| **Production Orders** | 6,234 | 8                                        | poNo, poDate, poETA, poReceivedDate, itemCode, itemQuantity, plasticResinCode, colorMasterbatchCode |
| **Production Records** | 61,185 | 18+                                      | recordDate, machineNo, itemCode, moldNo, itemGoodQuantity, itemTotalQuantity, itemCrack, itemShort, otherNG |


### 3.7. Data Preprocessing
Prior to analysis, the dataset underwent several preprocessing steps:

- **Data Cleaning**  
  - Removal of incomplete or corrupt records
  - Correction of inconsistent or outdated entries

- **Feature Engineering**  
  - Derived features such as production efficiency, machine utilization, and material ratios

- **Temporal Aggregation**  
  - Aggregated production records into daily, weekly, and monthly timeframes for trend analysis

- **Normalization**  
  - Standardized numerical attributes to ensure uniform feature scales across entities

### 3.8. Dataset Limitations
Despite its richness, the dataset has several limitations:

- **Seasonal Variability**  
  While the 27-month time span captures significant operational data, it may not fully represent long-term seasonal trends.

- **External Factors**  
  The dataset does not include external variables such as demand forecasts, raw material delays, or environmental impacts.

- **Facility Specificity**  
  The dataset is specific to a single production site and may not be directly applicable to facilities with differing technologies, workflows, or scales.