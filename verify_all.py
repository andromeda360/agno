try:
    import agno_v2
    print("agno_v2 imported")
    from agno_v2.os.app import AgentOS
    print("AgentOS imported")
    from agno_v2.os.routers.traces import get_traces_router
    print("traces imported")
    from agno_v2.workflow import DynamicParallel
    print("DynamicParallel imported")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)
