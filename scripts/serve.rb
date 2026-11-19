# Local compatibility for pathutil 0.16.x on Ruby 3 (keyword arguments).
require "pathutil"

if RUBY_VERSION.to_i >= 3 && Gem.loaded_specs.fetch("pathutil").version <= Gem::Version.new("0.16.2")
  class Pathutil
    def read(*args, **options)
      options[:encoding] ||= encoding
      content = File.read(self, *args, **options)
      normalize[:read] ? content.encode(universal_newline: true) : content
    end
  end
end

ARGV.unshift("serve")
load Gem.bin_path("jekyll", "jekyll")
