flowchart TD

%% Developer Interaction
A[Developer Push / Pull Request] --> B[GitHub Repository]

%% GitHub Automation Layer
B --> C[GitHub Actions CI Pipeline]

C --> D[Secret Audit Script]
C --> E[Python Build & Tests]
C --> F[Formatting Check (Black)]
C --> G[Dependabot Dependency Updates]
C --> H[CodeQL Security Analysis]
C --> I[Supply Chain Security (SBOM / Artifact Scan)]
C --> J[Release Automation]

%% Gate
D --> K{Security & CI Checks Pass?}
E --> K
F --> K
H --> K
I --> K

%% Deployment Auth
K -->|Approved| L[OIDC Token Issued by GitHub]

L --> M[Google Workload Identity Federation]

M --> N[Temporary IAM Credentials]

%% Build + Deploy
N --> O[Cloud Build Container Build]

O --> P[Artifact Registry Image]

P --> Q[Cloud Run Deployment]

%% Runtime
Q --> R[Enterprise-PQC-ZeroTrust-Core Service]

%% Monitoring / Security Feedback Loop
R --> S[Cloud Logging & Monitoring]
S --> C
