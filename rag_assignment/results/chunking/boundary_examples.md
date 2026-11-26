# Boundary examples (selected automatically from APP-deployment and SEC-pod-security-standards)

## fixed
**Good** - APP-deployment chunk 81 (800 chars, heading: none carried)

````text
and crowd the output of `kubectl get rs`. The configuration of each Deployment revision is stored in its ReplicaSets; therefore, once an old ReplicaSet is deleted, you lose the abi
[... 440 chars ...]
 field for pausing and resuming a Deployment. The only difference between
a paused Deployment and one that is not paused, is that any changes into the PodTemplateSpec of the paused
````

**Poor** - APP-deployment chunk 1 (800 chars, 195 tokens): mid-word cut

````text
in the background. Check the status of the rollout to see if it succeeds or not.
* [Declare the new state of the Pods](#updating-a-deployment) by updating the PodTemplateSpec of th
[... 440 chars ...]
nt to facilitate more load](#scaling-a-deployment).
* [Pause the rollout of a Deployment](#pausing-and-resuming-a-deployment) to apply multiple fixes to its PodTemplateSpec and the
````

**Good** - SEC-pod-security-standards chunk 35 (195 chars, heading: none carried)

````text
 isolated.

Additionally, the protection of sandboxed workloads is highly dependent on the method of
sandboxing. As such, no single recommended profile is recommended for all sandboxed workloads.
````

**Poor** - SEC-pod-security-standards chunk 0 (800 chars, 197 tokens): mid-word cut

````text
# Pod Security Standards

The Pod Security Standards define three different _policies_ to broadly cover the security
spectrum. These policies are _cumulative_ and range from highly
[... 440 chars ...]
lege escalations. Allows the default (minimally specified) Pod configuration. |
| <strong style="white-space: nowrap">Restricted</strong> | Heavily restricted policy, following cur
````

## recursive
**Good** - APP-deployment chunk 0 (597 chars, heading: none carried)

````text
# Deployments

A _Deployment_ provides declarative updates for Pods and
ReplicaSets.

You describe a _desired state_ in a Deployment, and the Deployment controller changes the actu
[... 237 chars ...]
 a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.

## Use Case

The following are typical use cases for Deployments:
````

**Poor** - APP-deployment chunk 19 (797 chars, 185 tokens): splits a code block (unbalanced ``` fence)

````text
* Get details of your Deployment:
  ```shell
  kubectl describe deployments
  ```
  The output is similar to this:
  ```
  Name:                   nginx-deployment
  Namespace:    
[... 437 chars ...]
late:
    Labels:  app=nginx
     Containers:
      nginx:
        Image:        nginx:1.16.1
        Port:         80/TCP
        Environment:  <none>
        Mounts:       <none>
````

**Good** - SEC-pod-security-standards chunk 2 (532 chars, heading: none carried)

````text
## Profile Details

### Privileged

**The _Privileged_ policy is purposely-open, and entirely unrestricted.** This type of policy is
typically aimed at system- and infrastructure-l
[... 172 chars ...]
cy applies, the Pod you define is able to bypass typical container isolation mechanisms.
For example, you can define a Pod that has access to the node's host network.

### Baseline
````

## structure
**Good** - APP-deployment chunk 0 (530 chars, heading: Deployments)

````text
# Deployments

A _Deployment_ provides declarative updates for Pods and
ReplicaSets.

You describe a _desired state_ in a Deployment, and the Deployment controller changes the actu
[... 170 chars ...]
with new Deployments.

**Note:**
Do not manage ReplicaSets owned by a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.
````

**Poor** - APP-deployment chunk 2 (5626 chars, 1398 tokens): exceeds 512 tokens, so the model silently truncates it

````text
## Creating a Deployment

The following is an example of a Deployment. It creates a ReplicaSet to bring up three `nginx` Pods:

[Code sample: controllers/nginx-deployment.yaml]

In
[... 5266 chars ...]
ts and StatefulSets). Kubernetes doesn't stop you from overlapping, and if multiple controllers have overlapping selectors those controllers might conflict and behave unexpectedly.
````

**Good** - SEC-pod-security-standards chunk 0 (836 chars, heading: Pod Security Standards)

````text
# Pod Security Standards

The Pod Security Standards define three different _policies_ to broadly cover the security
spectrum. These policies are _cumulative_ and range from highly
[... 476 chars ...]
 (minimally specified) Pod configuration. |
| <strong style="white-space: nowrap">Restricted</strong> | Heavily restricted policy, following current Pod hardening best practices. |
````

**Poor** - SEC-pod-security-standards chunk 2 (12511 chars, 4863 tokens): exceeds 512 tokens, so the model silently truncates it

````text
### Baseline

**The _Baseline_ policy is aimed at ease of adoption for common containerized workloads while
preventing known privilege escalations.** This policy is targeted at app
[... 12151 chars ...]
low_start_after_idle</code> (since Kubernetes 1.37)</li>
					<li><code>net.ipv4.tcp_notsent_lowat</code> (since Kubernetes 1.37)</li>
				</ul>
			</td>
		</tr>
	</tbody>
</table>
````

## semantic
**Good** - APP-deployment chunk 0 (530 chars, heading: none carried)

````text
# Deployments

A _Deployment_ provides declarative updates for Pods and
ReplicaSets.

You describe a _desired state_ in a Deployment, and the Deployment controller changes the actu
[... 170 chars ...]
with new Deployments.

**Note:**
Do not manage ReplicaSets owned by a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.
````

**Poor** - APP-deployment chunk 21 (1449 chars, 361 tokens): splits a code block (unbalanced ``` fence)

````text
## Rolling Back a Deployment

Sometimes, you may want to rollback a Deployment; for example, when the Deployment is not stable, such as crash looping.
By default, all of the Deploy
[... 1089 chars ...]
ell
  kubectl rollout status deployment/nginx-deployment
  ```

  The output is similar to this:
  ```
  Waiting for rollout to finish: 1 out of 3 new replicas have been updated...
````

**Good** - SEC-pod-security-standards chunk 0 (836 chars, heading: none carried)

````text
# Pod Security Standards

The Pod Security Standards define three different _policies_ to broadly cover the security
spectrum. These policies are _cumulative_ and range from highly
[... 476 chars ...]
 (minimally specified) Pod configuration. |
| <strong style="white-space: nowrap">Restricted</strong> | Heavily restricted policy, following current Pod hardening best practices. |
````

**Poor** - SEC-pod-security-standards chunk 3 (12205 chars, 4796 tokens): exceeds 512 tokens, so the model silently truncates it

````text
**Note:**
In this table, wildcards (`*`) indicate all elements in a list. For example,
`spec.containers[*].securityContext` refers to the Security Context object for _all defined
c
[... 11845 chars ...]
low_start_after_idle</code> (since Kubernetes 1.37)</li>
					<li><code>net.ipv4.tcp_notsent_lowat</code> (since Kubernetes 1.37)</li>
				</ul>
			</td>
		</tr>
	</tbody>
</table>
````

## structure_recursive
**Good** - APP-deployment chunk 0 (530 chars, heading: Deployments)

````text
# Deployments

A _Deployment_ provides declarative updates for Pods and
ReplicaSets.

You describe a _desired state_ in a Deployment, and the Deployment controller changes the actu
[... 170 chars ...]
with new Deployments.

**Note:**
Do not manage ReplicaSets owned by a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.
````

**Poor** - APP-deployment chunk 13 (1132 chars, 273 tokens): splits a code block (unbalanced ``` fence)

````text
* Get details of your Deployment:
  ```shell
  kubectl describe deployments
  ```
  The output is similar to this:
  ```
  Name:                   nginx-deployment
  Namespace:    
[... 772 chars ...]
eplicasAvailable
      Progressing    True    NewReplicaSetAvailable
    OldReplicaSets:  <none>
    NewReplicaSet:   nginx-deployment-1564180365 (3/3 replicas created)
    Events:
````

**Good** - SEC-pod-security-standards chunk 0 (836 chars, heading: Pod Security Standards)

````text
# Pod Security Standards

The Pod Security Standards define three different _policies_ to broadly cover the security
spectrum. These policies are _cumulative_ and range from highly
[... 476 chars ...]
 (minimally specified) Pod configuration. |
| <strong style="white-space: nowrap">Restricted</strong> | Heavily restricted policy, following current Pod hardening best practices. |
````

**Poor** - SEC-pod-security-standards chunk 13 (1225 chars, 588 tokens): exceeds 512 tokens, so the model silently truncates it

````text
<p><strong>Restricted Fields</strong></p>
				<ul>
					<li><code>spec.securityContext.sysctls[*].name</code></li>
				</ul>
				<p><strong>Allowed Values</strong></p>
				<ul>
			
[... 865 chars ...]
low_start_after_idle</code> (since Kubernetes 1.37)</li>
					<li><code>net.ipv4.tcp_notsent_lowat</code> (since Kubernetes 1.37)</li>
				</ul>
			</td>
		</tr>
	</tbody>
</table>
````

