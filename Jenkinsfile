
pipeline {
    agent none
    environment {
    WORKSPACE_DIR = "/home/jenkins/workspace/Taxonomy_NEW"
    DB_PATH       = "/home/jenkins/workspace/Taxonomy_NEW/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
    }
  stages {
    stage('Deploy Agent Script & Collect Logs') {
      agent { label 'agent' }
      steps {
      sh '''
        chmod -R 700 /home/jenkins/workspace/ || true
        echo "Copying agent to target..."
        scripts/collect_agent.py
      '''
    }
  }
    stage('Prioritize Artifacts') {
      agent { label 'agent' }
      steps {
        sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/priority_list.json'
      }
    }

    stage('Format and Split Logs') {
        agent { label 'agent' }
        steps {
        sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/output/artifacts.json --out ${WORKSPACE_DIR}/output/formatted_logs.json'
        sh 'python3 scripts/split_formatted_logs.py'
      }
    }  

    stage('Archive artifacts') {
      agent { label 'agent' }  
      steps {
        stash name: 'artifacts', includes: 'output/**'
        //archiveArtifacts artifacts: 'output/**', fingerprint: true
      }
    }
    stage('Copy artifacts to Master') {
      agent { label 'master' }  
      steps {
        unstash 'artifacts'
        archiveArtifacts artifacts: 'output/**', fingerprint: true

      }
    }      

    stage('Upload Reports to Azure Storage') {
      agent { label 'master' }    
      steps {
            script {
            withCredentials([
                string(credentialsId: 'TAXONOMY_STORAGE_ACCOUNT_KEY', variable: 'TAXONOMY_STORAGE_ACCOUNT_KEY')
                    ]) {
                sh '''
                # Set variables - REPLACE WITH YOUR ACTUAL STORAGE KEY
                STORAGE_ACCOUNT="taxonomystorage123"
                CONTAINER="reports"
                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/builds/$BUILD_NUMBER" --source output --overwrite
                az storage blob upload-batch --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --destination "reports/latest" --source output --overwrite
                '''
            }  
      }
    }        
    }
    
    stage('Export Mindmap') {
      steps {
        sh 'python3 scripts/mindmap_export.py --in ${WORKSPACE_DIR}/formatted_logs.json --out ${WORKSPACE_DIR}/mindmap.json'
      }
    }
  }
}
