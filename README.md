# Simple Lastpass Workflow for Alfred

Simple yet powerful integration with the Lastpass CLI so you can now get your passwords out of your Lastpass vault and straight into the clipboard from within Alfred.

## Installation

1. Ensure you have Alfred installed with the Alfred Powerpack License
2. Install Capture::Tiny
	1. Open up a Terminal Window
	2. run the command 'sudo cpan install Capture::Tiny'
	3. Accept the default options and ensure Capture::Tiny installs successfully
3. Install Homebrew (if you do not have it already installed)
	1. You should be able to just run the command in a terminal window (as your own user account NOT with sudo)
	2. ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
	3. Alternatively visit http://brew.sh/ for further instructions.
4. Install LastPass command line interface
	1. In a terminal window run
		brew install lastpass-cli --with-pinentry --with-doc
5. Download the .alfredworkflow file
6. Open the .alfredworkflow file to import into Alfred
7. Open up the workflow within Alfred, double click the top "Terminal Command" box in the workflow and change "yourloginemail@yourdomain.com" to your LastPass username.

## Usage

* lplogin - Log in to LastPass
* lplogout - Log out of LastPass
* lp <query> Search Lastpass vault for item containing <query>, press return to copy to clipboard.

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

Version 1.0 - Initial Release

## Credits

Created by [Stuart Ryan](http://stuartryan.com). If you would like to get into contact you can do so via:
* [@StuartCRyan on Twitter](http://twitter.com/stuartcryan)
* [Stuart Ryan on LinkedIn](https://au.linkedin.com/in/stuartcryan)
* [Technical Notebook Blog](http://technicalnotebook.com)
* [Technical Notebook Wiki](http://technicalnotebook.com/wiki)
* [Technical Notebook JIRA](http://technicalnotebook.com/jira)

## License

Released under the GNU GENERAL PUBLIC LICENSE Version 2, June 1991

## Notes
NOTE: This Alfred Workflow is not affiliated in any way with LastPass. The LastPass trademark and logo are owned by LastPass.com. The LastPass logo and product name have been used with permission of the LastPass team.

My thanks go out to LastPass for their awesome product and the new CLI!