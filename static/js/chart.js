function ChartData () {
    this.num = [];
    this.data = [];
    this.column = [];
    this.offset = 0;
}

ChartData.prototype.init = function(time, data, column) {
    this.column = column;
    for (let j = 0; j <= this.column.length - 1; j++) {
        this.data.unshift([]);
    }
    this.append(time, data);
}

ChartData.prototype.append = function(time, data) {
    this.offset += 1;
    for (let i = data.length - 1; i >= 0; i--) {
        for (let j = 0; j <= this.column.length - 1; j++) {
            this.data[j].unshift([time[i], data[i][j]]);
        }
    }
    this.num.unshift(data.length);
};

ChartData.prototype.pop = function() {
    if (this.offset <= 1) {
        return false;
    }
    this.offset -= 1;
    for (let j = 0; j <= this.column.length - 1; j++) {
        this.data[j] = this.data[j].slice(this.num[0]);
    }
    this.num.shift();
    return true;
};

ChartData.prototype.update = function(time) {
    let len = this.data[0].length;
    if (time > this.data[0][len - 1][0]) {
        return [-1, -1];
    }
    for (let i = len - 1; i >= 0; i--) {
        if ((this.data[0][i][0] > time) && (this.data[0][i - 1][0] <= time)) {
            return [i - 1, this.data[0][i - 1][0]];
        }
    }
    return [-1, -1];
}

function Chart (options) {
    this.chart = null;
    this.options = options;
    this.chartData = new ChartData();
}

Chart.prototype.init = function(time, data, column) {
    this.chartData.init(time, data, column);

    for (let j = 0; j <= this.chartData.column.length - 1; j++) {
        this.options.series[j].data = this.chartData.data[j];
        this.options.series[j].name = this.chartData.column[j];
        // this.options.series[j].yAxis = j;
    }
    this.chart = Highcharts.stockChart("chart", options);
}

Chart.prototype.append = function(time, data) {
    this.chartData.append(time, data);
    this.refresh();

    this.chart.xAxis[0].addPlotLine({
        value: this.chartData.data[0][this.chartData.num[0]][0],
        width: 2,
        color: "grey",
        dashStyle: "dash",
        id: this.chartData.offset
    });
}

Chart.prototype.pop = function() {
    if (this.chartData.pop()) {
        this.chart.xAxis[0].removePlotLine(this.chartData.offset + 1);
        this.refresh();
    }
}

Chart.prototype.refresh = function () {
    for (let j = 0; j <= this.chartData.column.length - 1; j++) {
        this.options.series[j].data = this.chartData.data[j];
        // this.options.series[j].visible = this.chart.series[j].visible;
    }
    this.chart = Highcharts.stockChart("chart", options);
}

Chart.prototype.update = function (time, data) {
    let ret = this.chartData.update(time);
    if (ret[0] === -1) {
        return;
    }
    let idx = ret[0];
    let t = ret[1];
    for (let j = 0; j <= this.chartData.column.length - 1; j++) {
        this.chart.series[j].removePoint(idx);
        this.chart.series[j].addPoint([t, data[j]]);
    }
}

Chart.prototype.getOffset = function() {
    return this.chartData.offset;
}