#!/home/ward/ruby/bin/ruby

require "cgi"
require "agile"

COL_COUNT = 3


##
# Helpers to format the principles consistenly
#
def pline(left, right)
  %{<li><font size="+1"><b>#{left}</b> over #{right}</font>
   }
end

def principles
  %{<table width="90%"><tr><td align="left"><ul>\n} +
    pline("Individuals and interactions", "processes and tools") +
    pline("Working software", "comprehensive documentation") +
    pline("Customer collaboration", "contract negotiation") +
    pline("Responding to change", "following a plan") +
    %{</ul></td></tr></table>}
end

##
# If there is more than one message directory, display a table of contents
#

def display_toc(cgi)
  res = ""
  index = Index.new
  index.each_message_dir do |md|
    res += %{<a href="display.cgi?ms=#{md.base_name}">#{md.date_range}</a> }
  end
  res
end


##
# The nav bar pops up if there is more than one directory. It allows
# users to scroll forwards and backwards chronologically through
# each directory

def show_nav_bar(message_dir_name)
  if message_dir_name
    index = Index.new
    before = index.entry_before(message_dir_name)
    after  = index.entry_after(message_dir_name)
  else
    before = after = nil
  end


  res = '<p><table align="center"><tr>'
  
  res += %{<td align="right" width="40%">} 
  if before
    res += "<a href=\"display.cgi?ms=#{before}\">" +
      "&lt;&lt;&nbsp;Previous&nbsp;</a>"
  else
    res += "&nbsp;"
  end
  res += "</td>\n"

  res += "<td align=\"center\" width=\"20%\">" +
    "<a href=\"display.cgi\">Index</a></td>\n"

  res += %{<td align="left" width="40%">} 
  if after
    res += "<a href=\"display.cgi?ms=#{after}\">&nbsp;Next&nbsp;>></a>"
  else
    res += "&nbsp;"
  end
  res += "</td>\n"
  
  res + "</tr></table>\n"
end


##
# Return an array of arrays, where the top level array is
# a set of columns, and each column contains a set
# of messages

def partition(messages)
  result = []
  COL_COUNT.times { result << [] }

  candidates = messages.dup

  total_size = 0
  messages.each {|m| total_size += m.display_size}
  column_size = (total_size + COL_COUNT - 1) / COL_COUNT

  available = column_size
  used = 0
  column = 0

  until candidates.empty?

    entry = candidates[0]

    # always try to use next available first
    if entry.display_size + used <= available
      result[column].push entry
      candidates.shift
    else
      # otherwise find first that fits
      found = false
      i = 1
      while !found and i < candidates.size
        entry = candidates[i]
        if entry.display_size + used <= available
          result[column].push entry
          candidates.delete_at(i)
          found = true
        end
        i += 1
      end
      # otherwise start a new column
      if !found
        available += column_size
        column += 1
        entry = candidates.shift
        result[column].push entry
      end
    end

    used += entry.display_size
  end

  result
end

def display_message_list(messages, message_dir_name=nil, date_range=nil)
  if date_range
    title = "Signatures Received: #{date_range}"
  else
    title = "All Signatories"
  end

  columns = partition(messages)

  res = '<table border="2" cellpadding="5"><tr><td colspan="3" align="center">'
  res += "<b>#{title}<b></td></tr>"

  res += '<tr valign="top">'
  columns.each do |col|
    res += "<td width=\"233\">" + (col.collect {|aMsg| aMsg.to_html}).join("<hr>\n")
  end

  res += '</td></tr></table>'
  res + show_nav_bar(message_dir_name)
end



def display_messages(cgi, message_dir_name)
  message_dir = MessageDir.existing(message_dir_name)
  messages = message_dir.messages
  display_message_list(messages, message_dir_name, message_dir.date_range)
end

##
# Display every message

def display_all_messages(cgi)
  index = Index.new
  messages = []
  index.message_dirs.collect do |dir_name|
    messages.concat MessageDir.existing(dir_name).messages
  end
  display_message_list(messages)
end

##
# Display the list of available messages by date range
# If there is only one data range available, just show it
#
def display_toc(cgi)
  index = Index.new
  if index.size == 0
    res = "<p>Be the first supporter!"
  elsif index.size == 1
    res = display_messages(cgi, index[0])
  else
    res = "Click on a date below to see the supporters " +
      "who signed up then.<p>"

    index.each_message_dir do |md|
      res += "<a href=\"display.cgi?ms=#{md.base_name}\">#{md.date_range}</a><br> "
    end

    res += "<p><a href=\"display.cgi?ms=all\">See all supporters</a>"
  end
  res
end

def signers(cgi)
  message_dir_name = cgi.params['ms'][0]    #  ["ms"][0] #.first
  if message_dir_name
    if message_dir_name == 'all'
      display_all_messages(cgi)
    else
      display_messages(cgi, message_dir_name)
    end
  else
    display_toc(cgi)
  end
end


cgi = CGI.new("html3")

cgi.out {
  cgi.html {
    cgi.head { cgi.title { "Agile Manifesto Signatories" } } +
      cgi.body('background' => "/background.jpg") {
      %{<center>
        <table width="70%">
        <tr><td>
        <font size="+3"><b>Independent Signatories of<br>
        The Manifesto for Agile Software Development</b></font>
        <p><font size="+1">
        We are uncovering better ways of developing
        software by doing it and helping others do it.
        Through this work we have come to value:</font><br>
       } + principles() +
      %{
        <br><font size="+1">That is, while there is value in the items on
        the right, we value the items on the left more.
        </font></td></tr>
        <tr><td>&nbsp;</td></tr>
        <tr><td align="center">Click <a href="signup.cgi">here</a> to add your
        name to the list of signatories.</td></tr>
        </table>
        <hr width="450" align="center"><p>
       } + signers(cgi) +
       %{</center>
       <script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
       </script>
       <script type="text/javascript">
       _uacct = "UA-2377314-1";
       urchinTracker();
       </script>
       }
    }
  }
}
