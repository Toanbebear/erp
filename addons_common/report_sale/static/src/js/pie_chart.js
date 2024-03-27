odoo.define('report_sale.pie_chart_with_percentage', function(require) {
    'use strict';

    var core = require('web.core');
    var Domain = require('web.Domain');
    var viewRegistry = require('web.view_registry');
    var Widget = require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var PieChart = require('web.PieChart');
    var qweb = core.qweb;
    var PieChart2 = PieChart.extend({

        start: function () {
            var data = this.controller.__parentedChildren[0].chart.dataPoints;

            var total = 0;
            for (var i = 0 ; i < data.length; i++){
                total += data[i].value
            }
            for (var i = 0 ; i < data.length; i++){
                data[i].labels[0] += " (" + parseFloat(data[i].value / total * 100).toFixed(2) + "%)";
            }

            this.$el.append(this.controller.$el);
            return this._super.apply(this, arguments);
        },

    });

    widgetRegistry.add('pie_chart_with_percentage', PieChart2);

    return PieChart2;
});

