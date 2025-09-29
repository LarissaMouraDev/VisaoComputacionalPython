// Esperar que o DOM seja completamente carregado
document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const uploadForm = document.getElementById('upload-form');
    const imageInput = document.getElementById('image-input');
    const imagePreview = document.getElementById('image-preview');
    const resultsSection = document.getElementById('results-section');
    const modelResult = document.getElementById('model-result');
    const plateResult = document.getElementById('plate-result');
    const conditionResult = document.getElementById('condition-result');
    const locationResult = document.getElementById('location-result');

    // Exibir preview da imagem quando selecionada
    imageInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
            };
            
            reader.readAsDataURL(file);
        }
    });

    // Manipular envio do formulário
    uploadForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const formData = new FormData(uploadForm);
        
        // Verificar se uma imagem foi selecionada
        if (imageInput.files.length === 0) {
            alert('Por favor, selecione uma imagem para análise.');
            return;
        }
        
        // Mostrar indicador de carregamento
        document.body.style.cursor = 'wait';
        
        // Enviar para o servidor
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Processar a resposta
            if (data.error) {
                alert('Erro: ' + data.error);
                return;
            }
            
            // Exibir resultados
            showResults(data.results);
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Ocorreu um erro ao processar a imagem. Tente novamente.');
        })
        .finally(() => {
            // Restaurar cursor
            document.body.style.cursor = 'default';
        });
    });

    // Função para exibir os resultados
    function showResults(results) {
        // Preencher os campos de resultado
        modelResult.textContent = results.modelo || 'Não detectado';
        plateResult.textContent = results.placa || 'Não detectado';
        conditionResult.textContent = results.estado || 'Não detectado';
        locationResult.textContent = results.localizacao || 'Não detectado';
        
        // Destaque para condição com cores
        if (results.estado) {
            if (results.estado === 'bom') {
                conditionResult.style.color = '#4CAF50'; // Verde
            } else {
                conditionResult.style.color = '#FFC107'; // Amarelo/laranja
            }
        }
        
        // Mostrar a seção de resultados
        resultsSection.classList.remove('hidden');
        
        // Rolar até os resultados
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
});