document.getElementById('transactionForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const type = document.querySelector('input[name="type"]:checked').value;
    const quantity = parseFloat(document.getElementById('quantity').value);
    const price = parseFloat(document.getElementById('price').value);
    processTransaction(type, quantity, price);
});

function getWallet() {
    return JSON.parse(localStorage.getItem('wallet') || '[]');
}

function setWallet(wallet) {
    localStorage.setItem('wallet', JSON.stringify(wallet));
    displayWallet();
}

function processTransaction(type, quantity, price) {
    let wallet = getWallet();
    let logEntry = `${type.toUpperCase()} ${quantity} at $${price}`;

    if (type === 'buy') {
        wallet.push({ quantity, price });
        logEntry += ' - Transaction added to wallet.';
    } else if (type === 'sell') {
        let remainingQuantity = quantity;
        wallet = wallet.map(item => {
            if (remainingQuantity > 0 && item.quantity > 0) {
                const sellQuantity = Math.min(item.quantity, remainingQuantity);
                logEntry += ` - Sold ${sellQuantity} from buy at $${item.price} for $${price}.`;
                remainingQuantity -= sellQuantity;
                item.quantity -= sellQuantity;
                logEntry += ` Profit/Loss per unit: $${price - item.price}.`;
            }
            return item;
        }).filter(item => item.quantity > 0);
    }

    setWallet(wallet);
    document.getElementById('transactionsLog').innerHTML += `<li>${logEntry}</li>`;
}

function displayWallet() {
    const wallet = getWallet();
    const walletList = document.getElementById('walletList');
    walletList.innerHTML = '';
    wallet.forEach(item => {
        walletList.innerHTML += `<li>${item.quantity} at $${item.price}</li>`;
    });
}

displayWallet();
