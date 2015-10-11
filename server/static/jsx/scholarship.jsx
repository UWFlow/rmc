define(
['ext/jquery', 'ext/react', 'ext/classnames', 'util'],
function($, React, classnames, util) {

  /* NEED: Generic expandable container
   * prof.js:75
   * Can give the number to show at the start
   * The React class to display
   * */

  var ScholarshipContainer = React.createClass({
    propTypes: {
      scholarshipData: React.PropTypes.array.isRequired
    },

    getInitialState: function() {
      return {
        expanded: false,
        minShow: 5,
        removedIds: []
      }
    },

    toggleExpand: function() {
      var self = this;

      if (this.state.expanded) {
        var navBarHeight = $("#site-nav").height();
        var margin = 16;
        var titleTop = $(React.findDOMNode(self.refs.title)).offset().top;
        $('html,body').animate({
          scrollTop: titleTop - navBarHeight - margin
        }, 300);

        $('.expanded-scholarships').fancySlide('up', 300, function() {
          self.setState({expanded: !self.state.expanded});
        });
      } else {
        $('.expanded-scholarships').fancySlide('down', 300, function() {
          self.setState({expanded: !self.state.expanded});
        });
      }
    },

    numHidden: function() {
      return this.props.scholarshipData.length - this.state.minShow -
          this.state.removedIds.length;
    },

    getFooter: function() {
      var footerSpan;
      if (!this.state.expanded) {
        footerText = 'See ' + this.numHidden() + ' more ' +
            util.pluralize(this.numHidden(), 'scholarship');
        footerSpan = <span>{footerText} &nbsp; <i className="icon-caret-down"></i></span>;
      } else {
        footerSpan = <span><i className="icon-caret-up"></i> &nbsp; Hide scholarships</span>;
      }

      var footer = (
        <div className="expand-footer" onClick={this.toggleExpand}>
          {footerSpan}
        </div>
      )

      if (this.props.scholarshipData.length <= this.state.minShow) {
        footer = (
          <div className="empty-footer">
          </div>
        )
      }

      return footer;
    },

    addRemovedId: function(i) {
      this.setState({removedIds: this.state.removedIds.concat([i])})
    },

    render: function() {
      var self = this;

      var visibleScholarships = this.props.scholarshipData.
          filter(function(s) {
            return self.state.removedIds.indexOf(s.id) === -1;
          }).
          slice(0, self.state.minShow).
          map(function(data, i) {
            return <ScholarshipBox key={data.id} data={data} onRemove={self.addRemovedId}/>
          }
      );

      var hiddenScholarships = this.props.scholarshipData.
          filter(function(s) {
            return self.state.removedIds.indexOf(s.id) === -1;
          }).
          slice(self.state.minShow).
          map(function(data, i) {
            return <ScholarshipBox key={data.id} data={data} onRemove={self.addRemovedId}/>
          }
      );

      if (this.props.scholarshipData.length == 0) {
        return null;
      }

      return (
        <div>
          <h1 ref="title" className="scholarships-header">
            Scholarships you may qualify for
          </h1>
          <div className="scholarship-container">
            {visibleScholarships}
            <div className="expanded-scholarships hide-initial">
              {hiddenScholarships}
            </div>
          </div>
          {this.getFooter()}
        </div>
      );
    }
  });

  var ScholarshipBoxInner = React.createClass({
    propTypes: {
      removeFromProfile: React.PropTypes.func.isRequired
    },

    render: function() {
      return (
        <div className="scholarship-inner row-fluid">
          <div className="span8 left-col">
            {this.props.data.description.replace('&amp;', 'and')}
          </div>
          <div className="span4 right-col">
            <ul>
              {this.props.data.eligibility.concat(
                  this.props.data.enrollment_year).map(function(req, i) {
                return (<li key={i}>{req}</li>);
              })}
            </ul>
          </div>
          <div className="row-fluid">
            <div className="span12 more-info">
              <a href={this.props.data.link} target="_blank">
                <i className="icon-info-sign"></i> More Info
              </a>
              <a onClick={this.props.removeFromProfile}>
                <i className="icon-remove-sign"></i> Remove from profile
              </a>
            </div>
          </div>
        </div>
      );
    }
  });

  var ScholarshipBox = React.createClass({
    propTypes: {
      data: React.PropTypes.shape({
        id: React.PropTypes.string.isRequired,
        title: React.PropTypes.string.isRequired,
        description: React.PropTypes.string.isRequired,
        eligibility: React.PropTypes.arrayOf(React.PropTypes.string),
        enrollment_year: React.PropTypes.arrayOf(React.PropTypes.string),
        link: React.PropTypes.string.isRequired
      }).isRequired
    },

    getInitialState: function() {
      return {
        expanded: false,
        removed: false
      }
    },

    toggleExpansion: function() {
      this.setState({expanded: !this.state.expanded});
    },

    removeFromProfile: function() {
      this.setState({removed: true});
      $.ajax({
        type: 'DELETE',
        url: '/api/v1/user/scholarships/' + this.props.data.id
      });
      this.props.onRemove(this.props.data.id);
    },

    render: function() {
      if (this.state.removed) {
        return null;
      }

      var classes = classnames({
        'scholarship-content': true,
        'expanded': this.state.expanded
      });

      scholarshipInner = null;

      if (this.state.expanded) {
        scholarshipInner = (<ScholarshipBoxInner data={this.props.data}
          removeFromProfile={this.removeFromProfile} />);
      }

      return (
        <div className={classes}>
          <div onClick={this.toggleExpansion} className="visible-section">
            <div className="scholarship-title">
              {this.props.data.title.replace('&amp;', 'and')}
            </div>
          </div>
          {scholarshipInner}
        </div>
      );
    }
  });

  return {
    ScholarshipContainer: ScholarshipContainer
  };
});
