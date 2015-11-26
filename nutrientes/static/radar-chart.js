var RadarChart = {
  draw: function(id, d, options){
  var cfg = {
      radius: 5,
      w: 600,
      h: 600,
      factor: 1,
      factorLegend: .85,
      levels: 3,
      maxValue: 0,
      radians: 2 * Math.PI,
      opacityArea: 0.5,
      ToRight: 5,
      TranslateX: 80,
      TranslateY: 30,
      ExtraWidthX: 100,
      ExtraWidthY: 100,
      color: d3.scale.category10(),
      legend: [],
      defaultValue: null,
      zoomOut: 1,
      radarClass: "radar-chart-serie-"
  };
      var polygonClass = "polygon." + cfg.radarClass;
      var circleClass = "circle." + cfg.radarClass;

      if('undefined' !== typeof options){
	  for(var i in options){
	      if('undefined' !== typeof options[i]){
		  cfg[i] = options[i];
	      }
	  }
      }

      if(cfg.legend.length == 0) {
          for(var i=0; i<d.length;i++) {
              cfg.legend.push("t" + i);
          }
      }

      cfg.maxValueD = {};
      for(var i=0; i<d[0].length;i++) {
	  cfg.maxValueD[d[0][i].axis] = 0;
      }
      
      if('object' == typeof cfg.maxValue) {
	  for (var key in cfg.maxValueD) {
              if (cfg.maxValueD.hasOwnProperty(key)) {
		  cfg.maxValueD[key] = d3.max(d, function(i){return d3.max(i.map(function(o){return key == o.axis ? o.value : 1;}))}) * cfg.zoomOut;
	      }
	  }
      }
      else {
	  cfg.maxValue = Math.max(cfg.maxValue, d3.max(d, function(i){return d3.max(i.map(function(o){return o.value;}))}));
	  for (var key in cfg.maxValueD) {
              if (cfg.maxValueD.hasOwnProperty(key)) {
		  cfg.maxValueD[key] = cfg.maxValue * cfg.zoomOut;
	      }
	  }
      }
      
      var allAxis = (d[0].map(function(i, j){return i.axis}));
      var total = allAxis.length;
      var radius = cfg.factor*Math.min(cfg.w/2, cfg.h/2);
      var Format = d3.format('');
      var FormatLevelValue = d3.format('.1f')
      d3.select(id).select("svg").remove();
      
      var g = d3.select(id)
	  .append("svg")
	  .attr("width", cfg.w+cfg.ExtraWidthX)
	  .attr("height", cfg.h+cfg.ExtraWidthY)
	  .append("g")
	  .attr("transform", 
		"translate(" + cfg.TranslateX + "," + cfg.TranslateY + ")");
      
      //Circular segments
      for(var j=0; j<cfg.levels-1; j++){
	  var levelFactor = cfg.factor*radius*((j+1)/cfg.levels);
	  g.selectAll(".levels")
	      .data(allAxis)
	      .enter()
	      .append("svg:line")
	      .attr("x1", function(d, i){return levelFactor*(1-cfg.factor*Math.sin(i*cfg.radians/total));})
	      .attr("y1", function(d, i){return levelFactor*(1-cfg.factor*Math.cos(i*cfg.radians/total));})
	      .attr("x2", function(d, i){return levelFactor*(1-cfg.factor*Math.sin((i+1)*cfg.radians/total));})
	      .attr("y2", function(d, i){return levelFactor*(1-cfg.factor*Math.cos((i+1)*cfg.radians/total));})
	      .attr("class", "line")
	      .style("stroke", "grey")
	      .style("stroke-opacity", "0.5")
	      .style("stroke-width", "0.3px")
	      .attr("transform", "translate(" + (cfg.w/2-levelFactor) + ", " + (cfg.h/2-levelFactor) + ")");
      }
	
      series = 0;
      
      var axis = g.selectAll(".axis")
	  .data(allAxis)
	  .enter()
	  .append("g")
	  .attr("class", "axis");
      
      for(var j=0; j<cfg.levels; j++){
          var levelFactor = cfg.factor*radius*((j+1)/cfg.levels);
	  g.selectAll(".levels")
	      .data(allAxis)
	      .enter()
	      .append("text")
	      .attr("class", "legend")
	      .text(function(d) {
		  return FormatLevelValue(((j+1)*cfg.maxValueD[d]/cfg.levels))})
	      .style("font-family", "sans-serif")
	      .style("font-size", "11px")
	      .attr("text-anchor", "middle")
	      .attr("dy", "1.5em")
	      .attr("fill", "#737373")
	      .attr("transform", "translate(" + (cfg.w/2-levelFactor+10) + ", " + (cfg.h/2-levelFactor-15) + ")")
	      .attr("x", function(d, i) {return levelFactor*(1-cfg.factor*Math.sin(i*cfg.radians/total))})
	      .attr("y", function(d, i) {return levelFactor*(1-cfg.factor*Math.cos(i*cfg.radians/total));})
      }  
      
      
      axis.append("line")
	  .attr("x1", cfg.w/2)
	  .attr("y1", cfg.h/2)
	  .attr("x2", function(d, i){return cfg.w/2*(1-cfg.factor*Math.sin(i*cfg.radians/total));})
	  .attr("y2", function(d, i){return cfg.h/2*(1-cfg.factor*Math.cos(i*cfg.radians/total));})
	  .attr("class", "line")
	  .style("stroke", "#c9c9c9")
	  .style("stroke-width", "2px");
      
      axis.append("text")
	  .attr("class", "legend")
	  .text(function(d){return d})
	  .style("font-family", "sans-serif")
	  .style("font-size", "12px")
	  .attr("text-anchor", "middle")
	  .attr("dy", "1.5em")
	  .attr("transform", function(d, i){return "translate(0, -10)"})
	  .attr("x", function(d, i){return cfg.w/2*(1-cfg.factorLegend*Math.sin(i*cfg.radians/total))-60*Math.sin(i*cfg.radians/total);})
	  .attr("y", function(d, i){return cfg.h/2*(1-Math.cos(i*cfg.radians/total))-20*Math.cos(i*cfg.radians/total);});
      
      
      d.forEach(function(y, x){
	  dataValues = [];
	  g.selectAll(".nodes")
	      .data(y, function(j, i){
		  dataValues.push([
		      cfg.w/2*(1-(parseFloat(Math.max(j.value, 0))/cfg.maxValueD[j.axis])*cfg.factor*Math.sin(i*cfg.radians/total)), 
		      cfg.h/2*(1-(parseFloat(Math.max(j.value, 0))/cfg.maxValueD[j.axis])*cfg.factor*Math.cos(i*cfg.radians/total))
		  ]);
	      });
	  dataValues.push(dataValues[0]);
	  g.selectAll(".area")
	      .data([dataValues])
	      .enter()
	      .append("polygon")
	      .attr("class", cfg.radarClass+series)
	      .style("stroke-width", "2px")
	      .style("stroke", cfg.color(series))
	      .attr("points",function(d) {
                  return d.map(function(d) {
		      return [d[0], d[1]].join(",");
		  }).join(" ");
	      })
	      .style("fill", function(j, i){return cfg.color(series)})
	      .style("fill-opacity", 0)
	  series++;
      });
      series=0;
      
      
      d.forEach(function(y, x){
	  g.selectAll(".nodes")
	      .data(y).enter()
	      .append("svg:circle")
	      .attr("class", cfg.radarClass+series)
	      .attr('r', cfg.radius)
	      .attr("alt", function(j){return Math.max(j.value, 0);})
	      .attr("cx", function(j, i){
		  dataValues.push([
		      cfg.w/2*(1-(parseFloat(Math.max(j.value, 0))/cfg.maxValueD[j.axis])*cfg.factor*Math.sin(i*cfg.radians/total)), 
		      cfg.h/2*(1-(parseFloat(Math.max(j.value, 0))/cfg.maxValueD[j.axis])*cfg.factor*Math.cos(i*cfg.radians/total))
		  ]);
		  return cfg.w/2*(1-(Math.max(j.value, 0)/cfg.maxValueD[j.axis])*cfg.factor*Math.sin(i*cfg.radians/total));
	      })
	      .attr("cy", function(j, i){
		  return cfg.h/2*(1-(Math.max(j.value, 0)/cfg.maxValueD[j.axis])*cfg.factor*Math.cos(i*cfg.radians/total));
	      })
	      .attr("data-id", function(j){return j.axis})
	      .style("fill", cfg.color(series)).style("fill-opacity", .2)
	      .on('mouseover', function (d){
		  z = "polygon."+d3.select(this).attr("class");
		  c = "circle."+d3.select(this).attr("class");
		  d3.selectAll(c).each(function(e, j) {
		      newX = parseFloat(d3.select(this).attr('cx')) - 10;
		      newY = parseFloat(d3.select(this).attr('cy')) - 5;
		      d3.select('text.tooltip-'+j)
			  .attr('x', newX)
			  .attr('y', newY)
			  //.text(Format(e.value))
			  .transition(200)
			  .style('opacity', 1);
		  });
		  default_data_show(z, c);
	      })
	      .append("svg:title")
	      .text(function(j){return j.axis + ": " + Math.max(j.value, 0)});
	  
	  series++;
      });
      
      default_data_show = function(z, c) {
	  g.selectAll("circle")
	      .transition(200)
	      .style("fill-opacity", 0.2);
	  g.selectAll("polygon")
	      .transition(200)
	      .style("fill-opacity", 0.0)
	      .style("stroke-opacity", 0.8);
          g.selectAll(z)
	      .transition(200)
	      .style("fill-opacity", cfg.opacityArea)
	      .style("stroke-opacity", 0.8);
	  g.selectAll(c)
	      .transition(200)
	      .style("fill-opacity", 0.9);
      }
      default_data_show(
	  polygonClass + cfg.legend.indexOf(cfg.defaultValue), 
	  circleClass + cfg.legend.indexOf(cfg.defaultValue));

      for(var i=0; i<d[0].length;i++) {
	  g.append('text')
	      .attr('class', 'tooltip-' + i)
	      .style('opacity', 0)
	      .style('font-family', 'sans-serif')
	      .style('font-size', '13px');
      }
      
     //legend
      var svg = d3.select('#text-chart')
	  .selectAll('svg')
	  .append('svg')
	  .attr("width", cfg.w+300)
	  .attr("height", cfg.h);
      
      //Create the title for the legend
      var text = svg.append("text")
	  .attr("class", "title")
	  .attr('transform', 'translate(90,0)') 
	  .attr("x", cfg.w - 10)
	  .attr("y", 20)
	  .attr("font-size", "12px")
	  .attr("fill", "#404040")
	  .text(cfg.legendText);
      
      //Initiate Legend	
      var legend = svg.append("g")
	  .attr("class", "legend")
	  .attr("height", 100)
	  .attr("width", 200)
	  .attr('transform', 'translate(90,20)');

      //Create colour squares
      legend.selectAll('rect')
	  .data(cfg.legend)
	  .enter()
	  .append("rect")
	  .attr("x", cfg.w - 10)
	  .attr("y", function(d, i){ return i * 20 + 5;})
	  .attr("width", 10)
	  .attr("height", 20)
	  .style("fill", function(d, i){ return cfg.color(i);})
          .on('click', function(d, i){
	      default_data_show(polygonClass + i, circleClass + i)
              d3.selectAll(circleClass+i).each(function(e, j) {
		  newX = parseFloat(d3.select(this).attr('cx')) - 10;
		  newY = parseFloat(d3.select(this).attr('cy')) - 5;
		  d3.select('text.tooltip-'+j)
		      .attr('x', newX)
		      .attr('y', newY)
		      //.text(Format(e.value))
		      .transition(200)
		      .style('opacity', 1);
              });
	  });
      
      //Create text next to squares
      legend.selectAll('text')
	  .data(cfg.legend)
	  .enter()
	  .append("text")
	  .attr("x", cfg.w + 5)
	  .attr("y", function(d, i){ return i * 20 + 19;})
	  .attr("font-size", "11px")
	  .attr("fill", "#737373")
	  .text(function(d) { return d; });
  }
};
