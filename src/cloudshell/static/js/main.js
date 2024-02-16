/*jslint browser:true */
var jQuery;
var wssh = {};

jQuery(function($){
  var style = {},
      default_fonts,
      DISCONNECTED = 0,
      CONNECTED = 2,
      state = DISCONNECTED,
      messages = {1: 'This client is connecting ...', 2: 'This client is already connnected.'},
      token = ''

  function parse_xterm_style() {
    var text = $('.xterm-helpers style').text();
    var arr = text.split('xterm-normal-char{width:');
    style.width = parseFloat(arr[1]);
    arr = text.split('div{height:');
    style.height = parseFloat(arr[1]);
  }

  function get_cell_size(term) {
    style.width = term._core._renderService._renderer.dimensions.actualCellWidth;
    style.height = term._core._renderService._renderer.dimensions.actualCellHeight;
  }

  function toggle_fullscreen(term) {
    $('#terminal .terminal').toggleClass('fullscreen');
    term.fitAddon.fit();
  }

  function current_geometry(term) {
    if (!style.width || !style.height) {
      try {
        get_cell_size(term);
      } catch (TypeError) {
        parse_xterm_style();
      }
    }

    var cols = parseInt(window.innerWidth / style.width, 10) - 1;
    var rows = parseInt(window.innerHeight / style.height, 10);
    return {'cols': cols, 'rows': rows};
  }

  function resize_terminal(term) {
    var geometry = current_geometry(term);
    term.on_resize(geometry.cols, geometry.rows);
  }

  function set_backgound_color(term, color) {
    term.setOption('theme', {
      background: color
    });
  }

  function set_font_color(term, color) {
    term.setOption('theme', {
      foreground: color
    });
  }

  function format_geometry(cols, rows) {
    return JSON.stringify({'cols': cols, 'rows': rows});
  }

  function read_as_text_with_decoder(file, callback, decoder) {
    var reader = new window.FileReader();

    if (decoder === undefined) {
      decoder = new window.TextDecoder('utf-8', {'fatal': true});
    }

    reader.onload = function() {
      var text;
      try {
        text = decoder.decode(reader.result);
      } catch (TypeError) {
        console.log('Decoding error happened.');
      } finally {
        if (callback) {
          callback(text);
        }
      }
    };

    reader.onerror = function (e) {
      console.error(e);
    };

    reader.readAsArrayBuffer(file);
  }

  function read_as_text_with_encoding(file, callback, encoding) {
    var reader = new window.FileReader();

    if (encoding === undefined) {
      encoding = 'utf-8';
    }

    reader.onload = function() {
      if (callback) {
        callback(reader.result);
      }
    };

    reader.onerror = function (e) {
      console.error(e);
    };

    reader.readAsText(file, encoding);
  }

  function read_file_as_text(file, callback, decoder) {
    if (!window.TextDecoder) {
      read_as_text_with_encoding(file, callback, decoder);
    } else {
      read_as_text_with_decoder(file, callback, decoder);
    }
  }

  function display_err() {}

  function init() {
    const currUrl = new URL(window.location.href)
    const params = new URLSearchParams(currUrl.search);
    const wsUrl = params.get("ws_url")

    var msg = {}
        var url = wsUrl, 
        sock = new window.WebSocket(url),
        encoding = 'utf-8',
        decoder = window.TextDecoder ? new window.TextDecoder(encoding) : encoding,
        terminal = document.getElementById('terminal'),
        termOptions = {
          cursorBlink: true,
          theme: {
            background: 'black',
            foreground: 'white'
          }
        };

    var term = new window.Terminal(termOptions);

    term.fitAddon = new window.FitAddon.FitAddon();
    term.loadAddon(term.fitAddon);

    msg.encoding = encoding;


    function term_write(text) {
      if (term) {
        term.write(text);
        if (!term.resized) {
          resize_terminal(term);
          term.resized = true;
        }
      }
    }

    function set_encoding(new_encoding) {
      // for console use
      if (!new_encoding) {
        console.log('An encoding is required');
        return;
      }

      if (!window.TextDecoder) {
        decoder = new_encoding;
        encoding = decoder;
        // console.log('Set encoding to ' + encoding);
      } else {
        try {
          decoder = new window.TextDecoder(new_encoding);
          encoding = decoder.encoding;
          //console.log('Set encoding to ' + encoding);
        } catch (RangeError) {
          console.log('Unknown encoding ' + new_encoding);
          return false;
        }
      }
    }

    wssh.set_encoding = set_encoding;
    set_encoding(msg.encoding);
    
    wssh.geometry = function() {
      // for console use
      var geometry = current_geometry(term);
      console.log('Current window geometry: ' + JSON.stringify(geometry));
    };

    wssh.send = function(data) {
      // for console use
      if (!sock) {
        console.log('Websocket was already closed');
        return;
      }

      if (typeof data !== 'string') {
        console.log('Only string is allowed');
        return;
      }

      try {
        JSON.parse(data);
        sock.send(data);
      } catch (SyntaxError) {
        data = data.trim() + 'source openrc.sh\r';
        sock.send(JSON.stringify({'data': data}));
      }
    };

    wssh.reset_encoding = function() {
      // for console use
      if (encoding === msg.encoding) {
        console.log('Already reset to ' + msg.encoding);
      } else {
        set_encoding(msg.encoding);
      }
    };

    wssh.resize = function(cols, rows) {
      // for console use
      if (term === undefined) {
        console.log('Terminal was already destroryed');
        return;
      }

      var valid_args = false;

      if (cols > 0 && rows > 0)  {
        var geometry = current_geometry(term);
        if (cols <= geometry.cols && rows <= geometry.rows) {
          valid_args = true;
        }
      }

      if (!valid_args) {
        console.log('Unable to resize terminal to geometry: ' + format_geometry(cols, rows));
      } else {
        term.on_resize(cols, rows);
      }
    };

    wssh.set_bgcolor = function(color) {
      set_backgound_color(term, color);
    };

    wssh.set_fontcolor = function(color) {
      set_font_color(term, color);
    };

    wssh.default_font = function() {
      term.setOption('fontFamily',  default_fonts);
      term.font_family_updated = false;
    };

    term.on_resize = function(cols, rows) {
      if (cols !== this.cols || rows !== this.rows) {
        // console.log('Resizing terminal to geometry: ' + format_geometry(cols, rows));
        this.resize(cols, rows);
        sock.send(JSON.stringify({'resize': [cols, rows]}));
      }
    };

    term.onData(function(data) {
      sock.send(JSON.stringify({'data': data}));
    });

    sock.onopen = function() {
      term.open(terminal);
      toggle_fullscreen(term);
      term.focus();
      state = CONNECTED;
      
      setTimeout(function () {
         // to init channel.
        sock.send(JSON.stringify({'auth': token}));
        sock.send(JSON.stringify({'data': ''}));
      }, 500);
      
    };

    sock.onmessage = function(msg) {
      read_file_as_text(msg.data, term_write, decoder);
    };

    sock.onerror = function(e) {
      console.error(e);
      window.parent.postMessage({
        evt: 'error'
      }, '*')
      $("body").css("background-color","black");
      $("body").append(`
        <p style="color:white;">
          Failed to connect CloudShell service.
        </p>.
      `)
    };

    sock.onclose = function(e) {
      console.log("session closed", e)
      window.parent.postMessage({
        evt: 'close'
      }, '*')

      term.dispose();
      term = undefined;
      sock = undefined;
      display_err()
      state = DISCONNECTED;
      $("body").css("background-color","black");
      $("body").append(`
        <p style="color:white;">
          Failed to connect CloudShell service.
        </p>.
      `)
    };

    $(window).resize(function(){
      if (term) {
        resize_terminal(term);
      }
    });
  }

  function connect() {
    window.onmessage = evt => {
      if(evt.origin == window.origin) {
        const { data } = evt
        token = data
      }
    }

    if (state !== DISCONNECTED) {
      console.log(messages[state]);
      return;
    }

    init()
  }

  wssh.connect = connect;

  // entry
  connect()
});
