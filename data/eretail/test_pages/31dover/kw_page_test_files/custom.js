jQuery(document).ready(function(){var $sidebar=jQuery(".sidebar"),$results=jQuery(".search_results_custom"),$window=jQuery(window),$offset=$sidebar.offset(),$form=jQuery("#search_mini_form"),$formOffset=$form.offset().top,$topPadding=5,$sidebarBottom=0,$windowBottom=0,$prevScroll=0;$window.scroll(function(){var $currScroll=$window.scrollTop();$sidebarBottom=$sidebar.offset().top+$sidebar.height();$resultsBottom=$results.offset().top+$results.height();if($window.height()>$sidebar.height()){if($window.scrollTop()>$offset.top&&$sidebarBottom<$resultsBottom){$sidebar.stop().animate({marginTop:getFacetTop($window.scrollTop(),$topPadding)})
}else{$sidebar.stop().animate({marginTop:0})}}else{if($currScroll>$prevScroll){$windowBottom=$window.scrollTop()+$window.height();if($windowBottom>$sidebarBottom){if($resultsBottom>$sidebarBottom){$sidebar.stop().animate({marginTop:getFacetTop($windowBottom,-$sidebar.height())})}else{$sidebar.stop().animate({marginTop:getFacetTop($resultsBottom,-$sidebar.height())})}}}else{if($window.scrollTop()>$offset.top){if($window.scrollTop()<$sidebar.offset().top){$sidebar.stop().animate({marginTop:getFacetTop($window.scrollTop(),$topPadding)})
}}else{$sidebar.stop().animate({marginTop:0})}}}$prevScroll=$currScroll});function getFacetTop($container,$facet){result=$container-$offset.top+$facet;if(result<0){result=0}return result}});