# Support library for the agile-supporters system

##
# General configuration
#
DATA_DIR = "/home/httpd/virt/agile/sign/data" # where to find pending and active dirs

##
# Class representing the content of a single message
# of support
#

class SupportMessage
  attr_accessor :name, :email, :publish_email, :comment, :date_created
  attr_accessor :org, :url

  def initialize(name="", email="", publish_email=false, org="", url="",
                 comment="", date_created="")

    @name          = name
    @email         = email
    @publish_email = publish_email
    @comment       = comment.chomp.gsub(/\r\n/, "\n")
    @date_created  = date_created
    @org           = org
    if url.length.zero? || url =~ %r{^http://}i
      @url         = url
    else
      @url         = "http://" + url
    end
    @wc = nil
  end

  ##
  # serialize ourselves to a file. We don't use Marshal because
  # we might want to manipulate flat files
  
  def to_file(path)
    File.open(path, "w") do |f|
      f.puts @name, @email, @publish_email, @date_created, 
        @org, @url, @comment
    end
  end

  ##
  # Create a new object from a file
  #
  def SupportMessage.from_file(path)
    File.open(path) do |f|
      name          = f.gets.chomp
      email         = f.gets.chomp
      publish_email = (f.gets.chomp == "true")
      date_created  = f.gets.chomp
      org           = f.gets.chomp
      url           = f.gets.chomp
      comment       = f.read.chomp
      return SupportMessage.new(name, email, publish_email, org, url, comment,
                                date_created)
    end
  end

  def to_html
    if @publish_email
      res = "<a href=\"mailto:#@email\">#@name</a>"
    else
      res = "<b>#@name</b>"
    end

    if @org.length + @url.length + @comment.length == 0
      res += "."
    else
      res += ": "
   
      if @org.length > 0 or @url.length > 0
        name = @org 
        name = url if name.length.zero?
        if @url.length > 0
          res += " (<a href=\"#@url\">#{name}</a>) "
        else
          res += " (" + name + ") "
        end
      end
      
      res + CGI.escapeHTML(@comment)
    end
  end

  def to_email
    res  = "  Name:         #@name\r\n"
    res << "  E-mail:       #@email"
    if @publish_email
      res << " (ok to use on site)\r\n"
    else
      res << " (do not use on site)\r\n"
    end
    res << "  Organization: #@org\r\n" if @org.length > 0
    res << "  Url:          #@url\r\n" if @url.length > 0
    res << "  Comment:\r\n      "
    res << @comment.split("\n").join("\r\n      ")
    res << "\r\n"
    res
  end

  ##
  # Comparison
  def ==(other)
    @name == other.name &&
      @email == other.email &&
      @publish_email == other.publish_email &&
      @date_created  == other.date_created &&
      @comment == other.comment
  end

  def spam?
    return true if @comment =~ /http:?\/\//
    false
  end

  ##
  # Return a rough indication of our size. This is simply the number of characters
  # displayed, plus '32' for the inter-message gap. We'll probably need
  # some tuning over time
  
  def display_size
    if !@size
      @size = @comment.size + @name.size + @org.size + 3
    end
    @size + 32
  end
end
  
##
# Handle the index of support messages
#

class Index
  INDEX_DIR = File.join(DATA_DIR, "active")
  
  ##
  # Return the full path to a particular message directory
  def Index.message_dir_name(base)
    File.join(Index::INDEX_DIR, base)
  end

  ##
  # Add a new message to the next available message directory
  def add_new(support_message)
    latest_dir = Dir.entries(INDEX_DIR).sort.grep(/\d/)[-1]
    if !latest_dir
      message_dir = MessageDir.create("000000001")
    else
      message_dir = MessageDir.existing(latest_dir)
      if message_dir.full?
        message_dir = MessageDir.create(latest_dir.succ)
      end
    end
    message_dir.add(support_message)
  end

  def dirlist
    @dirlist ||= Dir.entries(INDEX_DIR).grep(/\d/).sort
  end

  private :dirlist

  ##
  # Return all our message directories in order
  #
  def each_message_dir
    dirlist.each do |name|
      yield MessageDir.existing(name)
    end
  end

  ##
  # Find the entry before a given directory
  def entry_before(message_dir)
    pos = dirlist.index(message_dir) - 1
    pos >= 0 ? dirlist[pos] : nil
  end

  ##
  # Find the entry after a given directory
  def entry_after(message_dir)
    pos = dirlist.index(message_dir) + 1
    dirlist[pos]
  end

  ##
  # Return the number of directories
  def size
    dirlist.size
  end
  
  ##
  # Return a particular entry
  #
  def [](n)
    dirlist[n]
  end

  ##
  # Return them all
  def message_dirs
    dirlist
  end
end


##
# This is an individual directory containing up to MSG_DIR_MAX
# messages


class MessageDir

  TIMEFORMAT = "%d-%b-%y"

  MSG_DIR_MAX = 50

  attr_reader :base_name

  ## 
  # There's a wee parameter file in each message directory
  # holding
  #   - date of first message
  #   - date of last message

  class Params
    attr_reader :first_date, :last_date

    def initialize(dir_name)
      @file_name = File.join(dir_name, 'PARAMS')
      File.open(@file_name) do |f|
        @first_date = Time.at(f.gets.to_i)
        @last_date  = Time.at(f.gets.to_i)
      end
    rescue
      @first_date = @last_date = Time.now.to_i
    end

    def update
      File.open(@file_name, "w") do |f|
        f.puts @first_date.to_i
        f.puts Time.now.to_i
      end
    end
  end

  ##
  # Private constructor used by the create and existing
  # factories

  def initialize(base_name, dir_name)
    @base_name = base_name
    @dir_name  = dir_name
    @params    = Params.new(dir_name)
  end

  ##
  # create a new message dir with the given name

  def MessageDir.create(base_name)
    dir_name = Index.message_dir_name(base_name)
    Dir.mkdir(dir_name)
    return new(base_name, dir_name)
  end

  ##
  # Open an existing message directory
  #

  def MessageDir.existing(base_name)
    dir_name = Index.message_dir_name(base_name)
    return new(base_name, dir_name)
  end
    

  ##
  # Create new (unused) file name
  #

  def unused_name
    last_msg = Dir.entries(@dir_name).grep(/\d/).sort[-1] || "0000"
    last_msg.succ
  end
    

  ##
  # Add a new file to this directory
  #

  def add(support_message)
    this_msg = unused_name
    support_message.to_file(File.join(@dir_name, this_msg))
    @params.update
    this_msg
  end

  ##
  # See if the current directory is full. The '+3' accounts for
  # the entries '.', '..', and 'PARAMS'
  def full?
    Dir.entries(@dir_name).size >= MSG_DIR_MAX + 3
  end

  ##
  # Return the range of dates in this message directory
  #
  def date_range
    f = @params.first_date
    l = @params.last_date

    #if f.year != l.year
    #  f.strftime(TIMEFORMAT) + "..." + l.strftime(TIMEFORMAT)
    #elsif f.mon != l.mon
      f.strftime("%d %b") + " to " + l.strftime("%d %b %Y")
    #elsif f.day != l.day
    #  f.strftime("%d") + "..." + l.strftime("%d %b %y")
    #else
    #  l.strftime("%d %b %y")
    #end
  end


  ##
  # Return names
  def message_names
    Dir.entries(@dir_name).
      grep(/\d/).
      sort
  end

  ##
  # Return all our messages as an array
  #
  def messages
    message_names.collect {|name| message_content(name) }
  end

  ##
  # Return a particular message
  def message_content(name)
      SupportMessage.from_file(File.join(@dir_name, name))
  end

  
  def delete_message(msg)
    name = File.join(@dir_name, msg)
    begin
      File.unlink(name)
    rescue
    end
  end
end


#########################################################################

class ReviewDir < MessageDir

  def initialize
    super("", File.join(DATA_DIR, "review"))
  end

end

#########################################################################

class PendingDir < MessageDir

  def initialize
    super("", File.join(DATA_DIR, "pending"))
  end
  
  ##
  # Create new (unused) file name
  # (Make it ugly and hard to guess other names)
  #

  def unused_name
    begin
      name = rand(3**37).to_s
    end while File.exist?(name)
    name
  end
end

#########################################################################

