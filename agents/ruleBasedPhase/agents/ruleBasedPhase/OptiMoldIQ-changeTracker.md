# **ChangeTracking Agent**  

## **Role**  
- Tracks and logs all **modifications** to production records.  
- Ensures **changes are approved** before updating the main database.  
- Provides a **modification approval mechanism** for admins.  
- **Healing Mechanism**: Flags invalid changes, prevents incorrect updates, and suggests corrections.  

---

## **Inputs**  
- **productionStatus.xlsx** (Real-time production records)  
- **permissionControl.xlsx** (User permission settings)  
- **static database (moldInfo.xlsx, machineInfo.xlsx, etc.)** (Reference for validation)  
- **adminApprovals** (Manual approvals from authorized users)  

---

## **Process Flow**  

1. **Monitor production record changes** after each working shift.  
2. **Compare modified records** against existing production data.  
3. **Validate changes** based on:  
   - **Permission levels** (Ensures only authorized users can modify records).  
   - **Static database checks** (Cross-checks input with mold, machine, resin data, etc.).  
4. **Apply healing mechanism**:  
   - **Auto-correct minor errors** (e.g., wrong date format, missing spaces).  
   - **Flag invalid entries** (e.g., an unlisted machine number).  
   - **Suggest corrections** based on historical data or reference files.  
5. **Request admin approval for flagged changes** before updating records.  
6. **Generate reports** for change logs and approvals.  
7. **Update the production records** only after approval.  

---

## **Outputs (Reports)**  

### **1. Change Log Report (Main Output)**  
This report provides a **detailed history** of modifications made to production records.  

| Field            | Type       | Description                                              |
|-----------------|------------|----------------------------------------------------------|
| changeID        | varchar    | Unique identifier for the change.                        |
| timestamp       | timestamp  | Date and time of modification.                           |
| modifiedBy      | varchar    | User who made the modification.                          |
| permissionLevel | varchar    | User’s permission level.                                 |
| poNo           | varchar    | Purchase order related to the change.                   |
| itemCode       | varchar    | Item code associated with the modification.             |
| fieldChanged   | varchar    | Name of the field that was modified.                    |
| oldValue       | text       | Value before modification.                              |
| newValue       | text       | Value after modification.                               |
| changeStatus   | varchar    | Status (`Pending`, `Approved`, `Rejected`).             |
| reviewedBy     | varchar    | Admin who approved or rejected the change.              |
| reviewNotes    | text       | Comments from the admin on approval/rejection.          |

---

### **2. Unauthorized Modification Log (Error Report)**  
This report logs **unauthorized or invalid changes**, ensuring data security.  

| Field            | Type       | Description                                              |
|-----------------|------------|----------------------------------------------------------|
| logID          | varchar    | Unique identifier for the log entry.                     |
| timestamp      | timestamp  | Date and time of the flagged modification.               |
| modifiedBy     | varchar    | User who made the unauthorized change.                   |
| fieldChanged   | varchar    | Name of the field that was modified.                    |
| attemptedValue | text       | Value that was attempted to be entered.                 |
| issueType      | varchar    | Type of issue (`Unauthorized Change`, `Data Mismatch`). |
| correctiveAction | text     | Action taken (`Rejected`, `Flagged for Admin Review`).   |

---

## **Key Features**  
- **Modification approval system** to prevent unauthorized changes.  
- **Healing mechanism** to detect and reject invalid modifications.  
- **Logs all modifications**, ensuring full traceability.  
- **Real-time tracking of changes** after each working 
