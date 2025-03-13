// Main JavaScript for the Tiger Compiler Web UI

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror editor
    const editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        mode: 'tiger',
        theme: 'dracula',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        autoCloseBrackets: true,
        matchBrackets: true,
        lineWrapping: true
    });

    // Set default content
    editor.setValue('/* Welcome to the Tiger Compiler Web UI */\nlet\n\tvar x := 10\nin\n\tx\nend');

    // Get DOM elements
    const compileBtn = document.getElementById('compile-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const exampleSelect = document.getElementById('example-select');
    const errorModal = new bootstrap.Modal(document.getElementById('error-modal'));
    const errorMessage = document.getElementById('error-message');

    // Output elements
    const lexerOutput = document.getElementById('lexer-output');
    const parserOutput = document.getElementById('parser-output');
    const semanticOutput = document.getElementById('semantic-output');
    const irOutput = document.getElementById('ir-output');
    const canonIrOutput = document.getElementById('canon-ir-output');
    const assemblyOutput = document.getElementById('assembly-output');
    const regAllocOutput = document.getElementById('regalloc-output');
    const finalAssemblyOutput = document.getElementById('final-assembly-output');

    // Compile button click handler
    compileBtn.addEventListener('click', function() {
        const code = editor.getValue();
        if (!code.trim()) {
            showError('Please enter some code to compile.');
            return;
        }

        // Show loading state
        setLoadingState(true);

        // Fetch AST data
        fetch('/get_ast', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'code': code
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.ast) {
                // Update AST visualization
                window.astVisualizer.update(data.ast);
            }
        })
        .catch(error => {
            console.error('Error fetching AST:', error);
        });

        // Send code to server for compilation
        fetch('/compile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'code': code
            })
        })
        .then(response => response.json())
        .then(data => {
            setLoadingState(false);
            
            if (data.error) {
                showError(data.error.message);
                return;
            }
            
            // Update output tabs with results
            updateOutputs(data);
        })
        .catch(error => {
            setLoadingState(false);
            showError('An error occurred: ' + error.message);
        });
    });

    // Example selection handler
    exampleSelect.addEventListener('change', function() {
        const selectedExample = this.value;
        if (!selectedExample) return;

        fetch(`/get_example/${selectedExample}`)
            .then(response => response.json())
            .then(data => {
                if (data.content) {
                    editor.setValue(data.content);
                }
            })
            .catch(error => {
                showError('Error loading example: ' + error.message);
            });
    });

    // Upload button click handler
    uploadBtn.addEventListener('click', function() {
        fileUpload.click();
    });

    // File upload handler
    fileUpload.addEventListener('change', function() {
        if (this.files.length === 0) return;
        
        const file = this.files[0];
        if (!file.name.endsWith('.tig')) {
            showError('Please upload a .tig file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            
            if (data.content) {
                editor.setValue(data.content);
            }
        })
        .catch(error => {
            showError('Error uploading file: ' + error.message);
        });

        // Reset file input
        this.value = '';
    });

    // Helper function to update output tabs
    function updateOutputs(data) {
        // Lexer output
        if (data.lexer) {
            if (data.lexer.success) {
                lexerOutput.textContent = data.lexer.output.join('\n');
                lexerOutput.classList.remove('error-message');
            } else {
                lexerOutput.textContent = data.lexer.error;
                lexerOutput.classList.add('error-message');
            }
        }

        // Parser output
        if (data.parser) {
            if (data.parser.success) {
                parserOutput.textContent = data.parser.output;
                parserOutput.classList.remove('error-message');
            } else {
                parserOutput.textContent = data.parser.error;
                parserOutput.classList.add('error-message');
                // Show parser tab if there's an error
                document.getElementById('parser-tab').click();
            }
        }

        // Semantic output
        if (data.semantic) {
            if (data.semantic.success) {
                semanticOutput.textContent = data.semantic.output;
                semanticOutput.classList.remove('error-message');
            } else {
                semanticOutput.textContent = data.semantic.error;
                semanticOutput.classList.add('error-message');
                // Show semantic tab if there's an error
                document.getElementById('semantic-tab').click();
            }
        }

        // IR output
        if (data.ir) {
            if (data.ir.success) {
                irOutput.textContent = data.ir.output;
                irOutput.classList.remove('error-message');
            } else {
                irOutput.textContent = data.ir.error;
                irOutput.classList.add('error-message');
            }
        }

        // Canonized IR output
        if (data.canon_ir) {
            if (data.canon_ir.success) {
                canonIrOutput.textContent = data.canon_ir.output;
                canonIrOutput.classList.remove('error-message');
            } else {
                canonIrOutput.textContent = data.canon_ir.error;
                canonIrOutput.classList.add('error-message');
            }
        }

        // Assembly output
        if (data.assembly) {
            if (data.assembly.success) {
                assemblyOutput.textContent = data.assembly.output;
                assemblyOutput.classList.remove('error-message');
            } else {
                assemblyOutput.textContent = data.assembly.error;
                assemblyOutput.classList.add('error-message');
            }
        }

        // Register allocation output
        if (data.regalloc) {
            if (data.regalloc.success) {
                regAllocOutput.textContent = data.regalloc.output;
                regAllocOutput.classList.remove('error-message');
            } else {
                regAllocOutput.textContent = data.regalloc.error;
                regAllocOutput.classList.add('error-message');
            }
        }

        // Final assembly output
        if (data.final_assembly) {
            if (data.final_assembly.success) {
                finalAssemblyOutput.textContent = data.final_assembly.output;
                finalAssemblyOutput.classList.remove('error-message');
            } else {
                finalAssemblyOutput.textContent = data.final_assembly.error;
                finalAssemblyOutput.classList.add('error-message');
            }
        }
    }

    // Helper function to show error modal
    function showError(message) {
        errorMessage.textContent = message;
        errorModal.show();
    }

    // Helper function to set loading state
    function setLoadingState(isLoading) {
        if (isLoading) {
            compileBtn.innerHTML = '<span class="spinner"></span>Compiling...';
            compileBtn.disabled = true;
        } else {
            compileBtn.innerHTML = 'Compile';
            compileBtn.disabled = false;
        }
    }
}); 