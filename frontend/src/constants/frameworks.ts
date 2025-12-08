/**
 * All frameworks supported by Checkov
 */
export const SUPPORTED_FRAMEWORKS = [
  // IaC Frameworks
  { value: 'terraform', label: 'Terraform' },
  { value: 'terraform_json', label: 'Terraform JSON' },
  { value: 'terraform_plan', label: 'Terraform Plan' },
  { value: 'cloudformation', label: 'CloudFormation' },
  { value: 'arm', label: 'Azure ARM Templates' },
  { value: 'bicep', label: 'Azure Bicep' },
  
  // Container & Kubernetes
  { value: 'dockerfile', label: 'Dockerfile' },
  { value: 'kubernetes', label: 'Kubernetes' },
  { value: 'helm', label: 'Helm' },
  { value: 'kustomize', label: 'Kustomize' },
  
  // Configuration Management
  { value: 'ansible', label: 'Ansible' },
  
  // Serverless
  { value: 'serverless', label: 'Serverless Framework' },
  { value: 'cdk', label: 'AWS CDK' },
  
  // CI/CD
  { value: 'github_actions', label: 'GitHub Actions' },
  { value: 'github_configuration', label: 'GitHub Configuration' },
  { value: 'gitlab_ci', label: 'GitLab CI' },
  { value: 'gitlab_configuration', label: 'GitLab Configuration' },
  { value: 'azure_pipelines', label: 'Azure Pipelines' },
  { value: 'circleci_pipelines', label: 'CircleCI' },
  { value: 'bitbucket_pipelines', label: 'Bitbucket Pipelines' },
  { value: 'bitbucket_configuration', label: 'Bitbucket Configuration' },
  { value: 'argo_workflows', label: 'Argo Workflows' },
  
  // API & Config Files
  { value: 'openapi', label: 'OpenAPI/Swagger' },
  { value: 'json', label: 'JSON' },
  { value: 'yaml', label: 'YAML' },
] as const;

export type Framework = typeof SUPPORTED_FRAMEWORKS[number]['value'];

/**
 * Get framework label by value
 */
export function getFrameworkLabel(value: string): string {
  const framework = SUPPORTED_FRAMEWORKS.find(f => f.value === value);
  return framework?.label || value;
}

/**
 * Framework categories for better organization
 */
export const FRAMEWORK_CATEGORIES = {
  'Infrastructure as Code': ['terraform', 'terraform_json', 'terraform_plan', 'cloudformation', 'arm', 'bicep'],
  'Container & Kubernetes': ['dockerfile', 'kubernetes', 'helm', 'kustomize'],
  'Configuration Management': ['ansible'],
  'Serverless & Cloud': ['serverless', 'cdk'],
  'CI/CD Pipelines': [
    'github_actions', 'github_configuration',
    'gitlab_ci', 'gitlab_configuration',
    'azure_pipelines', 'circleci_pipelines',
    'bitbucket_pipelines', 'bitbucket_configuration',
    'argo_workflows'
  ],
  'API & Config': ['openapi', 'json', 'yaml'],
};
