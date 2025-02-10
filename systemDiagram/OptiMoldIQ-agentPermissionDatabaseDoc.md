# **Agent Permission Database Schema Documentation**

## **Table: agents**
Stores information about the agents in the system.

| Field       | Type      | Description                                   |
|------------|----------|-----------------------------------------------|
| agentId    | varchar  | Unique identifier for the agent.              |
| agentName  | varchar  | Name of the agent.                            |
| description | text     | Purpose of this agent.                        |
| createdAt  | timestamp | Date and time the agent was registered.       |

---

## **Table: agentRoles**
Defines roles specific to agents.

| Field     | Type      | Description                                   |
|----------|----------|-----------------------------------------------|
| roleId   | varchar  | Unique identifier for the role.               |
| roleName | varchar  | Descriptive name of the role.                 |

---

## **Table: agentPermissions**
Defines different permission types that can be granted to agents.

| Field         | Type      | Description                                    |
|--------------|----------|------------------------------------------------|
| permissionId | varchar  | Unique identifier for the permission.         |
| permissionName | varchar  | Descriptive name of the permission.         |
| description  | text     | Details about what this permission allows.    |

---

## **Table: agentRolePermissions**
Defines which permissions are assigned to each agent role.

| Field        | Type      | Description                                   |
|-------------|----------|-----------------------------------------------|
| roleId      | varchar  | Role identifier. (FK to `agentRoles`)         |
| permissionId | varchar  | Permission identifier. (FK to `agentPermissions`) |

---

## **Table: agentAssignments**
Maps agents to their respective roles and permissions.

| Field       | Type      | Description                                   |
|------------|----------|-----------------------------------------------|
| agentId    | varchar  | Unique identifier for the agent. (FK to `agents`) |
| roleId     | varchar  | Assigned role of the agent. (FK to `agentRoles`) |

---

## **Table: agentPermissionsOverride (Optional)**
Overrides specific permissions for individual agents.

| Field       | Type      | Description                                   |
|------------|----------|-----------------------------------------------|
| agentId    | varchar  | Agent identifier. (FK to `agents`)           |
| permissionId | varchar  | Permission identifier. (FK to `agentPermissions`) |
| overrideType | varchar  | Type of override (`grant`, `deny`).  