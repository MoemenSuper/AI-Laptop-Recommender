document.getElementById('recommendForm').addEventListener('submit', function(e) {
            e.preventDefault();
            getRecommendations();
        });
        
        async function getRecommendations() {
            const formData = new FormData(document.getElementById('recommendForm'));
            const data = {
                usage: formData.get('usage'),
                budget: formData.get('budget'),
                brand: formData.get('brand')
            };
            
            showLoading();
            
            try {
                const response = await fetch('/recommend', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result.recommendations, 'AI Recommendations');
                } else {
                    showError(result.error || 'Failed to get recommendations');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            }
        }
        
        async function searchLaptops() {
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) {
                showError('Please enter a search query');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result.results, 'Search Results');
                } else {
                    showError(result.error || 'Search failed');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            }
        }
        
        function displayResults(laptops, title) {
            hideLoading();
            hideError();
            
            document.getElementById('resultsTitle').textContent = title;
            const grid = document.getElementById('laptopGrid');
            
            if (laptops.length === 0) {
                grid.innerHTML = '<p>No laptops found. Try different search criteria.</p>';
            } else {
                grid.innerHTML = laptops.map(laptop => createLaptopCard(laptop)).join('');
            }
            
            document.getElementById('results').style.display = 'block';
        }
        
        function createLaptopCard(laptop) {
            const specs = laptop.specifications || {};
            const processor = specs.Processor || {};
            const memory = specs.Memory || {};
            const graphics = specs.Graphics || {};
            
            // Check if this is CSV data (has structured specs) or API data
            const hasStructuredSpecs = specs.cpu || specs.ram || specs.gpu || specs.price;
            
            return `
                <div class="laptop-card">
                    ${laptop.image && laptop.image !== 'Please upgrade your plan to get access to product images' ? `<img src="${laptop.image}" alt="${laptop.model}" onerror="this.style.display='none'">` : ''}
                    <div class="brand">${laptop.brand || 'Unknown Brand'}</div>
                    <h3>${laptop.model || 'Unknown Model'}</h3>
                    ${laptop.version ? `<p class="version"><strong>Version:</strong> ${laptop.version}</p>` : ''}
                    ${specs.price ? `<div class="price">${specs.price}</div>` : (laptop.price ? `<div class="price">$${laptop.price}</div>` : '')}
                    <div class="specs">
                        ${laptop.category ? `<p><strong>Category:</strong> ${laptop.category}</p>` : ''}
                        
                        ${hasStructuredSpecs ? `
                            ${specs.screen_size && specs.screen_size !== 'N/A' ? `<p><strong>Screen:</strong> ${specs.screen_size}" ${specs.resolution || ''}</p>` : ''}
                            ${specs.cpu && specs.cpu !== 'N/A' ? `<p><strong>CPU:</strong> ${specs.cpu}</p>` : ''}
                            ${specs.ram && specs.ram !== 'N/A' ? `<p><strong>RAM:</strong> ${specs.ram}</p>` : ''}
                            ${specs.storage && specs.storage !== 'N/A' ? `<p><strong>Storage:</strong> ${specs.storage}</p>` : ''}
                            ${specs.gpu && specs.gpu !== 'N/A' ? `<p><strong>GPU:</strong> ${specs.gpu}</p>` : ''}
                            ${specs.os && specs.os !== 'N/A' ? `<p><strong>OS:</strong> ${specs.os}</p>` : ''}
                            ${specs.weight && specs.weight !== 'N/A' ? `<p><strong>Weight:</strong> ${specs.weight}</p>` : ''}
                        ` : `
                            ${Object.keys(processor).length > 0 ? `<p><strong>Processor:</strong> ${Object.values(processor).join(', ')}</p>` : ''}
                            ${Object.keys(memory).length > 0 ? `<p><strong>Memory:</strong> ${Object.values(memory).join(', ')}</p>` : ''}
                            ${Object.keys(graphics).length > 0 ? `<p><strong>Graphics:</strong> ${Object.values(graphics).join(', ')}</p>` : ''}
                            ${!Object.keys(processor).length && !Object.keys(memory).length && !Object.keys(graphics).length && !hasStructuredSpecs ? '<p><em>Detailed specifications not available with current API plan</em></p>' : ''}
                        `}
                    </div>
                </div>
            `;
        }
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showError(message) {
            hideLoading();
            document.getElementById('error').textContent = message;
            document.getElementById('error').style.display = 'block';
            document.getElementById('results').style.display = 'none';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        // Allow Enter key to search
        document.getElementById('searchQuery').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchLaptops();
            }
        });
        
        // Chatbot Functions
        function toggleChatbot() {
            const container = document.getElementById('chatbotContainer');
            const toggle = document.getElementById('chatbotToggle');
            
            if (container.style.display === 'none' || container.style.display === '') {
                // Show chatbot with animation
                container.style.display = 'flex';
                setTimeout(() => {
                    container.classList.add('show');
                }, 10);
                
                // Hide toggle with animation
                toggle.style.transform = 'scale(0) rotate(180deg)';
                setTimeout(() => {
                    toggle.style.display = 'none';
                }, 300);
            } else {
                // Hide chatbot with animation
                container.classList.remove('show');
                setTimeout(() => {
                    container.style.display = 'none';
                }, 300);
                
                // Show toggle with animation
                toggle.style.display = 'block';
                setTimeout(() => {
                    toggle.style.transform = 'scale(1) rotate(0deg)';
                }, 10);
            }
        }
        
        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('chatbotInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const result = await response.json();
                
                // Hide typing indicator
                hideTyping();
                
                if (result.success) {
                    addMessage(result.response, 'bot');
                } else {
                    addMessage(result.error || 'Sorry, I encountered an error. Please try again.', 'bot');
                }
            } catch (error) {
                hideTyping();
                addMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'bot');
            }
        }
        
        function addMessage(message, type) {
            const messagesContainer = document.getElementById('chatbotMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            if (type === 'bot') {
                // Add typewriter effect for bot messages
                addMessageWithTypewriter(messageDiv, message, messagesContainer);
            } else {
                // Regular message for user
                messageDiv.textContent = message;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }
        
        function addMessageWithTypewriter(messageDiv, text, container) {
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
            
            // Ensure the message is visible (override the initial opacity: 0)
            messageDiv.style.opacity = '1';
            
            let index = 0;
            const speed = 25; // milliseconds per character
            
            function typeCharacter() {
                if (index < text.length) {
                    messageDiv.textContent = text.slice(0, index + 1);
                    index++;
                    setTimeout(typeCharacter, speed);
                } else {
                    // Remove any typewriter cursor effect
                    messageDiv.style.borderRight = 'none';
                }
                container.scrollTop = container.scrollHeight;
            }
            
            // Add initial cursor effect
            messageDiv.style.borderRight = '2px solid #ea580c';
            
            // Start typing after a short delay
            setTimeout(typeCharacter, 200);
        }
        
        function showTyping() {
            const typingIndicator = document.getElementById('typingIndicator');
            const messagesContainer = document.getElementById('chatbotMessages');
            
            typingIndicator.style.display = 'block';
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function hideTyping() {
            const typingIndicator = document.getElementById('typingIndicator');
            typingIndicator.style.display = 'none';
        }
        
        // API Status Monitoring
        async function checkApiStatus() {
            try {
                const response = await fetch('/api-status');
                const data = await response.json();
                
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                
                if (data.api_limit_reached) {
                    statusDot.className = 'status-dot status-csv';
                    statusText.textContent = `CSV Mode (${data.csv_laptop_count} laptops)`;
                } else {
                    statusDot.className = 'status-dot status-api';
                    statusText.textContent = 'API Mode';
                }
            } catch (error) {
                console.log('Status check failed:', error);
            }
        }
        
        // Check status every 30 seconds
        setInterval(checkApiStatus, 30000);
        
        // Check status on page load
        document.addEventListener('DOMContentLoaded', checkApiStatus);
        
        // Add reset API function (for testing)
        async function resetApiLimit() {
            try {
                const response = await fetch('/reset-api', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    console.log('API limit reset successfully');
                    checkApiStatus(); // Update status immediately
                }
            } catch (error) {
                console.log('Failed to reset API limit:', error);
            }
        }
        
        // Add click event to status indicator for manual reset (hidden feature)
        document.getElementById('statusIndicator').addEventListener('dblclick', function() {
            if (confirm('Reset API limit flag? (This will try API mode again)')) {
                resetApiLimit();
            }
        });
    
    