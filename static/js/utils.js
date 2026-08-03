
$(document).ready(function () {
    // Máscara para CPF
    $('#id_cpf').mask('000.000.000-00');

    // Máscara para telefone (celular ou fixo)
    $('#id_phone').mask('(00) 00000-0000');

    // Máscara para CEP - funciona com formsets
    $('input[id*="zipcode"]').mask('00000-000');

    // Validação simples de telefone
    $('#id_phone').on('blur', function () {
        const phone = $(this).val().replace(/\D/g, '');
        if (phone.length >= 10) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else if (phone.length > 0) {
            $(this).removeClass('is-valid').addClass('is-invalid');
        } else {
            $(this).removeClass('is-valid is-invalid');
        }
    });

    // Validação simples de CPF
    $('#id_cpf').on('blur', function () {
        const cpf = $(this).val().replace(/\D/g, '');
        if (cpf.length === 11) {
            $(this).removeClass('is-invalid').addClass('is-valid');
        } else if (cpf.length > 0) {
            $(this).removeClass('is-valid').addClass('is-invalid');
        } else {
            $(this).removeClass('is-valid is-invalid');
        }
    });

    // Função para aplicar máscaras em novos formsets adicionados dinamicamente
    function applyMasksToNewForms() {
        $('input[id*="zipcode"]').not('.masked').mask('00000-000').addClass('masked');
    }

    // Aplicar máscaras inicialmente
    applyMasksToNewForms();

    // Reaplicar máscaras quando novos formsets forem adicionados
    $(document).on('DOMNodeInserted', function () {
        applyMasksToNewForms();
    });
});

// Função para buscar CEP e preencher campos
function buscarCEP(cepInput) {
    const cep = cepInput.value.replace(/\D/g, '');

    if (cep.length !== 8) {
        return;
    }

    // Encontra o wrapper do formulário de endereço
    const formWrapper = cepInput.closest('.address-form-wrapper') || cepInput.closest('form');

    // Encontra os campos relacionados ao CEP
    const addressField = formWrapper.querySelector('input[id*="street"]') || formWrapper.querySelector('input[id*="street"]');
    const neighborhoodField = formWrapper.querySelector('input[id*="neighborhood"]');
    const cityField = formWrapper.querySelector('input[id*="city"]');
    const stateField = formWrapper.querySelector('input[id*="state"]');

    // Adiciona indicador de carregamento
    cepInput.classList.add('is-loading');
    cepInput.disabled = true;

    // Faz a requisição para a API
    fetch(`/integracoes/cep/?cep=${cep}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('CEP não encontrado');
            }
            return response.json();
        })
        .then(data => {
            // Preenche os campos com os dados retornados
            if (addressField && data.street) {
                addressField.value = data.street;
                addressField.classList.add('is-valid');
            }

            if (neighborhoodField && data.neighborhood) {
                neighborhoodField.value = data.neighborhood;
                neighborhoodField.classList.add('is-valid');
            }

            if (cityField && data.city) {
                cityField.value = data.city;
                cityField.classList.add('is-valid');
            }

            if (stateField && data.state) {
                stateField.value = data.state;
                stateField.classList.add('is-valid');
            }

            // Foca no campo de número
            const numberField = formWrapper.querySelector('input[id*="number"]');
            if (numberField) {
                numberField.focus();
            }

            // Remove indicador de carregamento
            cepInput.classList.remove('is-loading', 'is-invalid');
            cepInput.classList.add('is-valid');
        })
        .catch(error => {
            console.error('Erro ao buscar CEP:', error);
            cepInput.classList.add('is-invalid');
            alert('CEP não encontrado. Por favor, verifique o CEP digitado.');
        })
        .finally(() => {
            cepInput.disabled = false;
            cepInput.classList.remove('is-loading');
        });
}

$(document).ready(function () {
    // Event listener para buscar CEP ao sair do campo
    $(document).on('blur', 'input[id*="zipcode"]', function () {
        buscarCEP(this);
    });

    // Event listener para buscar CEP ao pressionar Enter
    $(document).on('keypress', 'input[id*="zipcode"]', function (e) {
        if (e.which === 13) {
            e.preventDefault();
            buscarCEP(this);
        }
    });
});
