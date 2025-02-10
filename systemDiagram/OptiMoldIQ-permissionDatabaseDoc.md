# **Permission Database Schema Documentation**

## **Table: users**
Stores user information and their associated roles.

| Field     | Type      | Description                                   |
|----------|----------|-----------------------------------------------|
| userId   | varchar  | Unique identifier for the user.               |
| username | varchar  | User’s login name.                            |
| email    | varchar  | User’s email address.                         |
| password | varchar  | Hashed password for authentication.           |
| roleId   | varchar  | Role assigned to the user. (FK to `userRoles`) |
| createdAt | timestamp | Date and time the user was created.         |
| updatedAt | timestamp | Date and time of the last update.           |

---

## **Table: userRoles**
Defines different roles and their associated permission levels.

| Field     | Type      | Description                                   |
|----------|----------|-----------------------------------------------|
| roleId   | varchar  | Unique identifier for the role.               |
| roleName | varchar  | Descriptive name of the role.                 |
| createdAt | timestamp | Date and time the role was created.         |

---

## **Table: permissions**
Defines various permissions available in the system.

| Field         | Type      | Description                                    |
|--------------|----------|------------------------------------------------|
| permissionId | varchar  | Unique identifier for the permission.         |
| permissionName | varchar  | Descriptive name of the permission.        |
| description  | text     | Details about what this permission allows.    |

---

## **Table: rolePermissions**
Defines which permissions are assigned to each role.

| Field        | Type      | Description                                    |
|-------------|----------|------------------------------------------------|
| roleId      | varchar  | Role identifier. (FK to `userRoles`)           |
| permissionId | varchar  | Permission identifier. (FK to `permissions`) |

---

## **Table: permissionsOverride (Optional)**
Overrides specific permissions for individual users.

| Field       | Type      | Description                                   |
|------------|----------|-----------------------------------------------|
| userId     | varchar  | User identifier. (FK to `users`)             |
| permissionId | varchar  | Permission identifier. (FK to `permissions`) |
| overrideType | varchar  | Type of override (`grant`, `deny`).         |

---

## **Table: roleHierarchy (Optional)**
Defines role relationships and inheritance.

| Field        | Type      | Description                                   |
|-------------|----------|-----------------------------------------------|
| roleId      | varchar  | Child role identifier. (FK to `userRoles`)   |
| parentRoleId | varchar  | Parent role identifier. (FK to `userRoles`) |

---

## **Table: auditLogs**
Tracks changes and user actions for security and monitoring.

| Field       | Type      | Description                                   |
|------------|----------|-----------------------------------------------|
| logId      | varchar  | Unique identifier for the log entry.         |
| userId     | varchar  | User who performed the action. (FK to `users`) |
| actionType | varchar  | Type of action (e.g., `update`, `delete`).    |
| description | text     | Detailed log description.                    |
| timestamp  | timestamp | Date and time of the action. 