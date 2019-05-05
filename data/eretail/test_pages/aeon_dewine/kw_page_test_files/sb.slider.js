function d(arg) { if(typeof console != 'undifined' && console.log) console.log(arg); }

!function( $ ){

  "use strict"

  var SbSlider = function ( element, options ) {
    this.options = $.extend({}, $.fn.sbslider.defaults, options)
    this.$element = $(element)
    this.$images = this.$element.find('.frame img').hide()
    this.$buttons = this.$element.find('.buttons a')
    $(this.$images[0]).show()

    this.current = 0
    this.next = 1


    this.$buttons.on('click', $.proxy(function(e) {
      e.preventDefault();
      var next = $(e.target).data('num')
      if (this.current == next) return
      swap.call(this, next)

    }, this))

    //run.call(this)
  }

  SbSlider.prototype = {
    constructor: SbSlider
  }

  function swap(next) {
    $(this.$images[this.current]).fadeOut(this.options.speed)
    $(this.$buttons[this.current]).removeClass('on')

    $(this.$images[next]).fadeIn(this.options.speed)
    $(this.$buttons[next]).addClass('on')

    this.current = next
  }

  function run() {
    var next = (this.current+1==this.$images.length) ? 0 : this.current+1;

    swap.call(this, next)

    setTimeout( $.proxy(run, this), this.options.interval )
  }

  $.fn.sbslider = function ( option ) {
    var $this = $(this)
      , data = $this.data('sbslider')
      , options = typeof option == 'object' && option

    if (!data) $this.data('sbslider', (data = new SbSlider(this, options)))
    if (typeof option == 'string') data[option]()

  }

  $.fn.sbslider.defaults = {
      interval: 1000,
      speed: 1000
  }



}( window.jQuery )
