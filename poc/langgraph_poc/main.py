"""Main entry point for the failure analysis POC."""
import argparse
import sys
from pathlib import Path
from . graph import run_failure_analysis
from .config import Config


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Analyze test failures using LangGraph and LLM'
    )
    
    parser.add_argument(
        '--xml-report',
        required=True,
        nargs='+',
        help='Path(s) to XML test report file(s) (e.g., test1.xml test2.xml)'
    )
    
    parser.add_argument(
        '--repo-path',
        required=True,
        help='Path to the local repository to analyze'
    )
    
    parser.add_argument(
        '--test-name',
        help='Name of the test run (optional)'
    )
    
    parser.add_argument(
        '--output',
        help='Path to save the analysis report (optional)'
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output showing detailed stage information'
    )
    
    parser.add_argument(
        '--debug',
        '-d',
        action='store_true',
        help='Enable debug mode with detailed logging and intermediate file saves'
    )
    
    parser.add_argument(
        '--debug-config',
        default='config/debug. yaml',
        help='Path to debug configuration file (default: config/debug.yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        print("Loading configuration...")
        if args.debug and Path(args.debug_config).exists():
            config = Config(args.debug_config)
            print(f"Debug mode enabled - using {args.debug_config}")
        else:
            config = Config(args.config)
        
        # Validate paths
        xml_paths = [args.xml_report] if isinstance(args.xml_report, str) else args.xml_report
        
        for xml_path in xml_paths:
            if not Path(xml_path).exists():
                print(f"XML report not found: {xml_path}")
                sys.exit(1)
        
        if not Path(args.repo_path). exists():
            print(f"Repository path not found: {args.repo_path}")
            sys.exit(1)
        
        # Set verbose mode
        verbose = args.verbose or args.debug
        if verbose and args.debug:
            print("\n" + "="*80)
            print("DEBUG MODE ENABLED - Detailed stage tracking and file logging")
            print("="*80 + "\n")
        elif verbose:
            print("\n" + "="*80)
            print("VERBOSE MODE ENABLED - Detailed stage tracking")
            print("="*80 + "\n")
        
        # Run analysis
        final_state = run_failure_analysis(
            xml_report_paths=xml_paths,
            repo_path=args.repo_path,
            test_name=args.test_name,
            config=config,
            verbose=verbose,
            debug=args.debug
        )
        
        # Print results
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        
        if final_state.get('workflow_status') == 'error':
            print(f"\nAnalysis failed: {final_state.get('error_message', 'Unknown error')}")
            
            if args.debug:
                print("\nDebug information saved to:")
                print("   debug/debug.log")
                print("   debug/intermediate/")
            
            sys.exit(1)
        
        # Print report to console
        if final_state.get('final_report'):
            print("\n" + final_state['final_report'])
            
            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(final_state['final_report'], encoding='utf-8')
                print(f"\nReport saved to: {args.output}")
        
        # Print debug file locations
        if args.debug:
            print("\nDebug files saved to:")
            print("   Log: debug/debug.log")
            print("   Intermediate files: debug/intermediate/")
            if args.output:
                print(f"   Report: {args.output}")
        
        # Print summary if debug logger exists
        debug_logger = final_state.get('_debug_logger')
        if debug_logger:
            debug_logger.summary()
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        
        if args.debug:
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
            print("\nCheck debug/debug.log for more details")
        
        sys. exit(1)


if __name__ == '__main__':
    main()