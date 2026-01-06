document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('game-grid');
    const ctx = canvas.getContext('2d');

    const startButton = document.getElementById('start-button');
    const stopButton = document.getElementById('stop-button');
    const resetButton = document.getElementById('reset-button');
    const randomizeButton = document.getElementById('randomize-button');
    const speedSlider = document.getElementById('speed-slider');

    const resolution = 20;
    let grid;
    let animationId;
    let isRunning = false;
    let speed = speedSlider.value;

    function setupGrid() {
        canvas.width = Math.floor(canvas.parentElement.clientWidth / resolution) * resolution;
        canvas.height = 500;
        grid = createGrid(canvas.width / resolution, canvas.height / resolution);
        drawGrid();
    }

    function createGrid(cols, rows) {
        return new Array(cols).fill(null)
            .map(() => new Array(rows).fill(0));
    }

    function randomizeGrid() {
        for (let col = 0; col < grid.length; col++) {
            for (let row = 0; row < grid[col].length; row++) {
                grid[col][row] = Math.round(Math.random());
            }
        }
        drawGrid();
    }

    function drawGrid() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#eee';
        for (let col = 0; col < grid.length; col++) {
            for (let row = 0; row < grid[col].length; row++) {
                const cell = grid[col][row];
                ctx.beginPath();
                ctx.rect(col * resolution, row * resolution, resolution, resolution);
                ctx.fillStyle = cell ? 'black' : 'white';
                ctx.fill();
                ctx.stroke();
            }
        }
    }

    function nextGen() {
        const nextGrid = createGrid(grid.length, grid[0].length);
        for (let col = 0; col < grid.length; col++) {
            for (let row = 0; row < grid[col].length; row++) {
                const neighbors = countNeighbors(col, row);
                const cell = grid[col][row];
                if (cell === 1 && (neighbors < 2 || neighbors > 3)) {
                    nextGrid[col][row] = 0;
                } else if (cell === 0 && neighbors === 3) {
                    nextGrid[col][row] = 1;
                } else {
                    nextGrid[col][row] = cell;
                }
            }
        }
        return nextGrid;
    }

    function countNeighbors(x, y) {
        let count = 0;
        for (let i = -1; i < 2; i++) {
            for (let j = -1; j < 2; j++) {
                if (i === 0 && j === 0) continue;
                const col = (x + i + grid.length) % grid.length;
                const row = (y + j + grid[0].length) % grid[0].length;
                count += grid[col][row];
            }
        }
        return count;
    }

    function update() {
        if (!isRunning) {
            return;
        }
        grid = nextGen();
        drawGrid();
        setTimeout(() => {
            animationId = requestAnimationFrame(update);
        }, speed);
    }

    function start() {
        if (!isRunning) {
            isRunning = true;
            update();
        }
    }

    function stop() {
        isRunning = false;
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    }

    function reset() {
        stop();
        grid = createGrid(grid.length, grid[0].length);
        drawGrid();
    }

    canvas.addEventListener('click', (event) => {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const col = Math.floor(x / resolution);
        const row = Math.floor(y / resolution);
        if (grid[col] && grid[col][row] !== undefined) {
            grid[col][row] = grid[col][row] ? 0 : 1;
            drawGrid();
        }
    });

    startButton.addEventListener('click', start);
    stopButton.addEventListener('click', stop);
    resetButton.addEventListener('click', reset);
    randomizeButton.addEventListener('click', () => {
        stop();
        randomizeGrid();
    });
    speedSlider.addEventListener('input', (e) => {
        speed = 1050 - e.target.value;
    });
    
    window.addEventListener('resize', () => {
        stop();
        setupGrid();
    });

    // Initial setup
    setupGrid();
});
