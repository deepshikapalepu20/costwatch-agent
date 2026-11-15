pipeline {
  agent any
 
  parameters {
    string(name: 'EC2_HOST', defaultValue: '', description: 'EC2 public IP (leave blank to skip deploy)')
    booleanParam(name: 'ENFORCE_GATE', defaultValue: true, description: 'Fail the build on CRITICAL vulnerabilities')
  }
 
  environment {
    DH    = credentials('dockerhub-creds')
    IMAGE = "${DH_USR}/costwatch-agent"
    TAG   = "${env.BUILD_NUMBER}"
  }
 
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
 
    stage('Secrets Scan (Gitleaks)') {
      steps {
        sh 'gitleaks detect --source . --report-format json --report-path gitleaks-report.json'
      }
    }
 
    stage('Static Analysis (Bandit)') {
      steps {
        sh 'bandit -r costwatch -f json -o bandit-report.json || true'
        sh 'bandit -r costwatch -lll'
      }
    }
 
    stage('Unit Tests') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -q -r requirements.txt pytest httpx
          PYTHONPATH="$WORKSPACE" python -m pytest -q
        '''
      }
    }
 
    stage('Build Image') {
      steps { sh 'docker build -t $IMAGE:$TAG .' }
    }
 
    stage('Image Scan (Trivy)') {
      steps {
        sh 'trivy image --severity HIGH,CRITICAL --format json -o trivy-image-report.json $IMAGE:$TAG'
      }
    }
 
    stage('Vulnerability Gate') {
      when { expression { params.ENFORCE_GATE } }
      steps {
        sh 'trivy image --severity CRITICAL --ignore-unfixed --exit-code 1 $IMAGE:$TAG'
      }
    }
 
    
    stage('IaC Scan (Trivy)') {
        steps {
            sh '''
                trivy config --format json -o trivy-terraform-report.json terraform
                trivy config --format json -o trivy-cloudformation-report.json cloudformation
            '''
        }
    }

 
    stage('Terraform Validate') {
      steps {
        dir('terraform') {
          sh 'terraform init -backend=false && terraform validate'
        }
      }
    }
 
    stage('Push Image') {
      steps {
        sh '''
          echo "$DH_PSW" | docker login -u "$DH_USR" --password-stdin
          docker push $IMAGE:$TAG
        '''
      }
    }
 
    stage('Deploy to EC2') {
      when { expression { params.EC2_HOST?.trim() } }
      steps {
        sshagent(credentials: ['ec2-ssh-key']) {
          sh 'ssh -o StrictHostKeyChecking=accept-new ec2-user@$EC2_HOST "sudo bash /opt/costwatch/deploy.sh $IMAGE:$TAG"'
        }
      }
    }
 
    stage('Smoke Test') {
      when { expression { params.EC2_HOST?.trim() } }
      steps {
        sh 'sleep 20 && curl -f http://$EC2_HOST:8000/health'
      }
    }
  }
 
  post {
    always {
      archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
    }
  }
}
