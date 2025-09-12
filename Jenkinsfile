pipeline {
  agent any
  environment {
    WORKSPACE_DIR = "${env.WORKSPACE}/forensic_workspace"
    DB_PATH       = "${env.WORKSPACE}/forensic_workspace/metadata.db"
    GRAFANA_FORENSIC_DIR = "/var/lib/grafana/forensic"
  }

  stages {
    stage('Initialize') {
      steps {
        echo 'Preparing workspace...'
        sh 'mkdir -p ${WORKSPACE_DIR}'
        sh 'python3 scripts/initialize.py --workspace ${WORKSPACE_DIR}'
      }
    }

    stage('Deploy Agent Script & Ensure Target Dir') {
      steps {
        withCredentials([
          string(credentialsId: 'TARGET_IP', variable: 'TARGET_IP'),
          string(credentialsId: 'SSH_CRED_ID', variable: 'SSH_CRED_ID')
        ]) {
          withCredentials([sshUserPrivateKey(credentialsId: "${SSH_CRED_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
            sh '''
              echo "Creating target forensic dir..."
              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "mkdir -p /home/$SSH_USER/forensic && chmod 700 /home/$SSH_USER/forensic || true"

              echo "Copying agent to target..."
              scp -i $SSH_KEY -o StrictHostKeyChecking=no scripts/collect_agent.py $SSH_USER@$TARGET_IP:/home/$SSH_USER/forensic/collect_agent.py

              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "chmod +x /home/$SSH_USER/forensic/collect_agent.py"
            '''
          }
        }
      }
    }

    stage('Run Agent on Target (collect live data)') {
      steps {
        withCredentials([
          string(credentialsId: 'TARGET_IP', variable: 'TARGET_IP'),
          string(credentialsId: 'SSH_CRED_ID', variable: 'SSH_CRED_ID')
        ]) {
          withCredentials([sshUserPrivateKey(credentialsId: "${SSH_CRED_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
            sh '''
              echo "Running agent remotely..."
              ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP "python3 /home/$SSH_USER/forensic/collect_agent.py --out /tmp/artifacts.json"

              echo "Copying artifacts back to controller workspace..."
              scp -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP:/tmp/artifacts.json ${WORKSPACE_DIR}/artifacts.json
            '''
          }
        }
      }
    }

    stage('Prioritize Artifacts') {
      steps {
        sh 'python3 scripts/prioritize.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/priority_list.json'
      }
    }

stage('Collect Forensics') {
    steps {
        sh '''
            ssh -i $SSH_KEY -o StrictHostKeyChecking=no $SSH_USER@$TARGET_IP \
              "python3 /home/$SSH_USER/forensic/collect_agent.py --out /tmp/artifacts.json"
            scp -i $SSH_KEY -o StrictHostKeyChecking=no \
              $SSH_USER@${TARGET_IP}:/tmp/artifacts.json artifacts.json
        '''
    }
}

    
    stage('Format Logs') {
      steps {
        sh 'python3 scripts/format_json.py --in ${WORKSPACE_DIR}/artifacts.json --out ${WORKSPACE_DIR}/formatted_logs.json'
      }
    }

    stage('Store Metadata') {
      steps {
        sh 'python3 scripts/store_metadata.py --db ${DB_PATH} --meta ${WORKSPACE_DIR}/priority_list.json'
      }
    }

    stage('Push to Grafana (Simulated)') {
      steps {
        sh '''
          python3 scripts/push_grafana.py --in ${WORKSPACE_DIR}/formatted_logs.json --out ${WORKSPACE_DIR}/grafana_payload.json
          echo "Copying artifacts.json into Grafana directory..."
          sudo cp ${WORKSPACE}//forensic_workspace/artifacts.json ${GRAFANA_FORENSIC_DIR}/artifacts.json
          sudo chown grafana:grafana ${GRAFANA_FORENSIC_DIR}/artifacts.json
          sudo chmod 640 ${GRAFANA_FORENSIC_DIR}/artifacts.json
          '''
      }
    }

    stage('Upload Reports to Azure Storage') {
      steps {
            script {
            withCredentials([
                string(credentialsId: 'TAXONOMY_STORAGE_ACCOUNT_KEY', variable: 'TAXONOMY_STORAGE_ACCOUNT_KEY')
                    ]) {
                sh '''
                # Set variables - REPLACE WITH YOUR ACTUAL STORAGE KEY
                STORAGE_ACCOUNT="taxonomystorage123"
                CONTAINER="reports"
          
                # Upload to build-specific path
                az storage blob upload --container-name $CONTAINER --name "builds/$BUILD_NUMBER/artifacts.json" --file forensic_workspace/artifacts.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                az storage blob upload --container-name $CONTAINER --name "builds/$BUILD_NUMBER/formatted_logs.json" --file forensic_workspace/formatted_logs.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite

                # Upload to 'latest' path
                az storage blob upload --container-name $CONTAINER --name "latest/artifacts.json" --file forensic_workspace/artifacts.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
                az storage blob upload --container-name $CONTAINER --name "latest/formatted_logs.json" --file forensic_workspace/formatted_logs.json --account-name $STORAGE_ACCOUNT --account-key "$TAXONOMY_STORAGE_ACCOUNT_KEY" --overwrite
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

    stage('Notify & Archive') {
      steps {
        echo 'Archiving artifacts...'
        archiveArtifacts artifacts: 'forensic_workspace/**', fingerprint: true
      }
    }
  }
}
