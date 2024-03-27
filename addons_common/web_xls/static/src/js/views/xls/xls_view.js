odoo.define('web_xls.XlsView', function (require) {
	"use strict";

	var XlsController = require('web_xls.XlsController');
	var XlsModel = require('web_xls.XlsModel');
	var XlsRenderer = require('web_xls.XlsRenderer');
	var AbstractView = require('web.AbstractView');
	var viewRegistry = require('web.view_registry');
	var BasicView = require('web.BasicView');
	
	var XlsView = BasicView.extend({
		icon: 'fa-file-excel-o',
	    config: _.extend({}, BasicView.prototype.config,{
	        Model: XlsModel,
	        Controller: XlsController,
	        Renderer: XlsRenderer,
	    }),
	    cssLibs: [
	        '/web_xls/static/lib/xspreadsheet/src/css/xspreadsheet.css'
	    ],
	    jsLibs: [
	        '/web_xls/static/lib/xspreadsheet/src/js/xspreadsheet.js',
	    ],
	    viewType: 'xls',
	    groupable: false,

	    init: function () {
	        this._super.apply(this, arguments);
	        var view_fields = []
	        var viewID;
	        this.controllerParams.actionViews.forEach(function (action) {
	        	if (action.type == 'xls'){
	        		viewID = action.viewID;
	        	}
	        });
	        this.arch.children.forEach(function (child) {
	        	view_fields.push(child.attrs.name)
	        });
	        this.loadParams.view_fields = view_fields;
	        this.loadParams.viewID = viewID;
	        this.loadParams.model_name = this.controllerParams.modelName;
	        this.loadParams.fields = this.fields;
	    },
	    
	});

	viewRegistry.add('xls', XlsView);
	return XlsView;

});


	