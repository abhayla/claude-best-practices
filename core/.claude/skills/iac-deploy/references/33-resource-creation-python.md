# 3.3 Resource Creation — Python

### 3.3 Resource Creation — Python

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = pulumi.get_stack()
project_name = pulumi.get_project()

