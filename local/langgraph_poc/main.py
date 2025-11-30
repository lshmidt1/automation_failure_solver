"""Main entry point for the LangGraph POC."""
import argparse
import sys
from pathlib import Path
from .config import Config
from .graph import run_failure_analysis


def main():
    """Main function to run the failure analysis POC."""
    parser = argparse.ArgumentParser(
        description='Analyze test failures using LangGraph (Local XML + Local Repo)'
    )
    parser.add_argument(
        '--xml-report',
        required=True,
        help='Path to XML test report file (e.g., test-results.xml)'
    )
    parser.add_argument(
        '--repo-path',
        required=True,
        help='Path to local repository containing the code'
    )
    parser.add_argument(
        '--test-name',
        help='Optional test identifier/name for reference'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--output',
        help='Output file for the analysis report'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate paths
        if not Path(args.xml_report).exists():
            print(f"❌ XML report not found: {args.xml_report}")
            sys.exit(1)
        
        if not Path(args.repo_path).exists():
            print(f"❌ Repository path not found: {args.repo_path}")
            sys.exit(1)
        
        # Load configuration
        print("Loading configuration...")
        config = Config(args.config)
        
        # Run the analysis
        final_state = run_failure_analysis(
            xml_report_path=args.xml_report,
            repo_path=args.repo_path,
            test_name=args.test_name,
            config=config
        )
        
        # Print results
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80 + "\n")
        
        if final_state.get('final_report'):
            print(final_state['final_report'])
            
            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(final_state['final_report'])
                print(f"\n✅ Report saved to: {args.output}")
        else:
            print("❌ No report generated")
            if final_state.get('error_message'):
                print(f"Error: {final_state['error_message']}")
            sys.exit(1)
        
        print("\n✅ Analysis workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
