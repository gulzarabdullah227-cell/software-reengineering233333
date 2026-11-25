pipeline {
    agent any

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        PYTHON_EXE = 'C:\\Users\\PMLS\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
        APP_PORT = '8088'
        DEPLOY_DIR = 'C:\\ProgramData\\Jenkins\\astrobot-live'
        PYTHONUTF8 = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'git log -1 --oneline'
            }
        }

        stage('Verify Environment') {
            steps {
                bat '''
                    set "PY=python"
                    if exist "%PYTHON_EXE%" set "PY=%PYTHON_EXE%"
                    "%PY%" --version
                '''
            }
        }

        stage('Build') {
            steps {
                bat '''
                    set "PY=python"
                    if exist "%PYTHON_EXE%" set "PY=%PYTHON_EXE%"
                    "%PY%" -m py_compile astrobot\\app.py astrobot\\build.py astrobot\\test_app.py
                    "%PY%" astrobot\\build.py
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                    set "PY=python"
                    if exist "%PYTHON_EXE%" set "PY=%PYTHON_EXE%"
                    "%PY%" -m unittest discover -s astrobot -p "test_*.py" -v
                '''
            }
        }

        stage('Deploy Live') {
            steps {
                withEnv(['JENKINS_NODE_COOKIE=dontKillMe', 'BUILD_ID=dontKillMe']) {
                    bat 'powershell -NoProfile -ExecutionPolicy Bypass -File deploy.ps1 -PythonExe "%PYTHON_EXE%" -Port %APP_PORT% -DeployDir "%DEPLOY_DIR%"'
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'index.html,astrobot/preview.html,AstroBot_preview.html', allowEmptyArchive: true
        }
        success {
            echo "AstroBot CI/CD succeeded! Live app: http://localhost:${env.APP_PORT}"
        }
        failure {
            echo 'AstroBot CI/CD pipeline failed. Review the stage logs above.'
        }
    }
}
