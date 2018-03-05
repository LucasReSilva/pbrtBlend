pipeline {
  agent any
  stages {
    stage('Version check') {
      parallel {
        stage('Blender') {
          steps {
            sh '''/home/lucas/Documentos/TCC/Blender/blender -v
'''
          }
        }
        stage('PBRTv3') {
          steps {
            sh 'wget https://gist.github.com/LucasReSilva/40dc265ccaaf04dc0cb6e2c81c7dbb0e/raw/8cd87f29a67e496222688eb46281b3ffe5e4c623/PBRTv3_Exemple'
            sh 'pbrt PBRTv3_Exemple --quick'
          }
        }
      }
    }
    stage('Export file') {
      steps {
        sh 'wget "https://github.com/LucasReSilva/Cornell-Box/raw/master/Blender%20files/Cycles.blend"'
        sh '/home/lucas/Documentos/TCC/Blender/blender -b -E help && /home/lucas/Documentos/TCC/Blender/blender -b Cycles.blend --addons'
        sh '/home/lucas/Documentos/TCC/Blender/blender -b Cycles.blend -E PBRTv3_RENDER -f 1  --python /home/lucas/Documentos/TCC/blendToPBRTv3.py'
      }
    }
    stage('Render scene') {
      steps {
        sh 'pbrt /tmp/untitled.Scene.00001.PBRTv3s'
      }
    }
    stage('Compare') {
      steps {
        sh 'wget http://www.graphics.cornell.edu/online/box/box.jpg'
        sh ' convert box.jpg -resize 500x500 box_resized.png'
        sh 'composite cornell-box.png box_resized.png -compose difference difference.png'
      }
    }
  }
}