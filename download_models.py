import urllib.request
import os
import sys

def download_file(url, filepath):
    """Download arquivo com barra de progresso"""
    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        bar_length = 50
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        sys.stdout.write(f'\r[{bar}] {percent:.1f}% ({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB)')
        sys.stdout.flush()
    
    print(f"\nBaixando: {os.path.basename(filepath)}")
    try:
        urllib.request.urlretrieve(url, filepath, show_progress)
        print(f"\n✓ {os.path.basename(filepath)} baixado com sucesso!")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao baixar {os.path.basename(filepath)}: {e}")
        return False

def main():
    print("="*60)
    print("DOWNLOAD DOS ARQUIVOS YOLO")
    print("="*60)
    
    # Criar pasta models se não existir
    os.makedirs('models', exist_ok=True)
    
    files = {
        'models/yolov3.weights': {
            'url': 'https://pjreddie.com/media/files/yolov3.weights',
            'size': '237 MB'
        },
        'models/yolov3.cfg': {
            'url': 'https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg',
            'size': '8 KB'
        },
        'models/coco.names': {
            'url': 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names',
            'size': '1 KB'
        }
    }
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    for filepath, info in files.items():
        if os.path.exists(filepath):
            print(f"\n○ {os.path.basename(filepath)} já existe (pulando)")
            skipped += 1
        else:
            if download_file(info['url'], filepath):
                downloaded += 1
            else:
                failed += 1
    
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"✓ Baixados: {downloaded}")
    print(f"○ Já existiam: {skipped}")
    if failed > 0:
        print(f"✗ Falhas: {failed}")
    print("="*60)
    
    if failed == 0 and (downloaded > 0 or skipped == len(files)):
        print("\n✓ Todos os arquivos estão prontos!")
        print("Execute: python main.py")
    else:
        print("\n⚠ Alguns arquivos não foram baixados.")
        print("Tente baixar manualmente ou verifique sua conexão.")

if __name__ == "__main__":
    main()