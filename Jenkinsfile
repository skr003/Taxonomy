pipeline {
    agent none
    environment {
    WORKSPACE_DIR = "/home/jenkins/workspace/Taxonomy_NEW"
    MASTER_WORKSPACE_DIR = "/var/lib/jenkins/workspace/Taxonomy_NEW"
    DB_PATH       = "/home/jenkins/workspace/Taxonomy_NEW/output/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
    FORENSIC_AGENT = "/home/jenkins/forensic/collect_agent.py"
    LOKI_URL = "http://172.16.0.4:3100/loki/api/v1/push"
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
        stash name: 'artifacts', includes: 'output/**'    
      }
    }   
        stage('Format Logs') {
            agent { label 'master' } 
            steps {
                unstash 'artifacts'
                archiveArtifacts artifacts: 'output/**', fingerprint: true  
                sh '''
                mkdir -p ${MASTER_WORKSPACE_DIR}/output/loki_logs
                for file in ${MASTER_WORKSPACE_DIR}/output/split_logs/*.json; do
                    echo "[+] Processing $file"
                    python3 scripts/format_for_loki.py --in $file --out-dir output/loki_logs
                done
                '''
            }
        }
        stage('Push to Loki') {
            agent { label 'master' }             
            steps {
                  sh '''
                     for file in output/loki_logs/*.json; do
                        echo "[+] Pushing \$file to Loki..."
                          curl -s -X POST -H "Content-Type: application/json" \
                              --data-binary @\${file} \
                                http://172.16.0.4:3100/loki/api/v1/push || true
                       done
                   '''
            }
        }
        stage('Visualization') {
            agent { label 'master' }  
            steps {
                sh """
                    echo "[+] Visualization available in Grafana + Loki dashboards"
                """
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
  }
}
