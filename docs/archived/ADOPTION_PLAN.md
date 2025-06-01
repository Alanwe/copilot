# Azure Components Foundry - New Spec Adoption Plan

## Overview
This document outlines the plan to migrate from the current individual component deployment approach to the new unified container + dispatcher architecture as specified in `new-spec.md`.

## Migration Strategy

### Phase 1: Foundation Migration (Weeks 1-2)

#### 1.1 Create New Architecture Structure
- [ ] Create `runtime/` directory with dispatcher and adapters
- [ ] Create `deploy/` directory with templates and orchestrator
- [ ] Migrate to YAML-based manifest format
- [ ] Create unified Dockerfile

#### 1.2 Implement Core Runtime Components
- [ ] Dispatcher with HANDLER environment variable support
- [ ] Unified adapters for each Azure service
- [ ] Component registration and discovery system

#### 1.3 Template Infrastructure
- [ ] Azure ML online/batch deployment templates
- [ ] Azure Functions deployment templates
- [ ] Container Apps deployment templates
- [ ] Template token replacement system

### Phase 2: Component Migration (Weeks 3-4)

#### 2.1 Component Interface Standardization
- [ ] Ensure all components implement predict(payload) function
- [ ] Add component metadata and defaults files
- [ ] Update component structure to new standards

#### 2.2 Manifest Migration
- [ ] Convert existing JSON manifest to new YAML format
- [ ] Group components by deployment environments
- [ ] Add override configurations per environment

#### 2.3 Build System
- [ ] Create Makefile for unified build process
- [ ] Implement container image tagging with Git SHA
- [ ] Container registry integration

### Phase 3: Deployment Migration (Weeks 5-6)

#### 3.1 Orchestrator Implementation
- [ ] Create deploy/run.py orchestrator script
- [ ] Implement Azure CLI integration
- [ ] Add parallel deployment capabilities
- [ ] Environment-specific subscription switching

#### 3.2 CI/CD Integration
- [ ] Update GitHub Actions for new deployment flow
- [ ] Implement container build and push pipeline
- [ ] Add manifest validation and deployment triggers

#### 3.3 Testing and Validation
- [ ] Component functionality testing in new architecture
- [ ] End-to-end deployment testing
- [ ] Performance validation

### Phase 4: Documentation and Training (Week 7)

#### 4.1 Documentation Updates
- [ ] Update component development guidelines
- [ ] Create deployment operation guides
- [ ] Update user instructions

#### 4.2 Migration Guide
- [ ] Create step-by-step migration guide for existing components
- [ ] Document troubleshooting procedures
- [ ] Create rollback procedures

## Success Criteria

### Technical Metrics
- [ ] Single container image can host all components
- [ ] One-command deployment to multiple environments
- [ ] Deployment time reduced by 50%
- [ ] Code duplication eliminated in adapters and infrastructure

### Operational Metrics
- [ ] Manifest becomes single source of truth for deployments
- [ ] Non-technical stakeholders can modify deployments via manifest
- [ ] Deployment consistency across environments improved
- [ ] Rollback time reduced to < 5 minutes

## Risk Mitigation

### High-Risk Items
1. **Component Compatibility**: Some components may not fit predict(payload) pattern
   - *Mitigation*: Create adapter layer for complex components
   
2. **Performance Impact**: Dispatcher overhead
   - *Mitigation*: Benchmark and optimize hot paths
   
3. **Deployment Complexity**: New orchestrator may have bugs
   - *Mitigation*: Extensive testing, gradual rollout, maintain old scripts as fallback

### Migration Strategy
- Maintain parallel systems during transition
- Component-by-component migration with validation
- Keep existing deployment scripts as backup during transition

## Implementation Details

### New Directory Structure
```
repo/
├─ components/                   # Existing components (minimal changes)
├─ runtime/                      # NEW: Runtime adapters and dispatcher
│   ├─ dispatcher.py
│   ├─ azureml_adapter.py
│   ├─ function_adapter.py
│   ├─ containerapp_adapter.py
│   └─ mcp_adapter.py
├─ deploy/                       # NEW: Deployment orchestration
│   ├─ manifest.yaml            # NEW: YAML-based deployment manifest
│   ├─ run.py                   # NEW: Deployment orchestrator
│   └─ templates/               # NEW: Infrastructure templates
│       ├─ aml-online.yml
│       ├─ aml-batch.yml
│       ├─ function.json
│       └─ containerapp.bicep
├─ Dockerfile                   # NEW: Unified container image
├─ Makefile                     # NEW: Build automation
└─ admin/                       # UPDATED: Enhanced management scripts
```

### Key Technical Decisions

1. **Backwards Compatibility**: Maintain existing component structure, add new runtime layer
2. **Gradual Migration**: Components can be migrated one at a time
3. **Fallback Strategy**: Keep existing deployment scripts during transition
4. **Testing Strategy**: Parallel deployment testing before cutover

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 | Weeks 1-2 | Runtime foundation, templates, unified Dockerfile |
| 2 | Weeks 3-4 | Component migration, new manifest format |
| 3 | Weeks 5-6 | Orchestrator, CI/CD updates, testing |
| 4 | Week 7 | Documentation, training, go-live |

**Total Duration**: 7 weeks

## Next Steps

1. Review and approve this adoption plan
2. Begin Phase 1 implementation
3. Set up regular review checkpoints
4. Establish success metrics tracking
